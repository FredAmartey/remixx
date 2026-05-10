"""Remixx FastAPI backend.

Endpoints:
  POST /chat       — SSE stream of agent steps + final result
  POST /taste      — extract profile from seed songs, recommend
  POST /playlist   — generate playlist with narrative arc tagging
  GET  /personas   — list of available DJ voices
  GET  /catalog/{id} — single track lookup
  GET  /healthz    — liveness check

No persistence; each request is independent.
"""
from __future__ import annotations

import asyncio
import json
import json as _json
import logging
import threading
import time
from pathlib import Path
from queue import Queue
from typing import Annotated, Any

import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

from app.agent import run_agent, _catalog, _retr
from app.db import init_db, create_session, add_message, save_playlist, list_playlists
from app.guardrails import compute_confidence, is_prompt_injection
from app.personas import PERSONAS, commentary as persona_commentary, taste_commentary
from app.rag import CATALOG
from app.reranker import infer_query_overrides, rerank


# ── Structured logging ─────────────────────────────────────────────────────

class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "level": record.levelname,
            "msg": record.getMessage(),
            "name": record.name,
        }
        if record.args and isinstance(record.args, dict):
            payload.update(record.args)
        return _json.dumps(payload)


_handler = logging.StreamHandler()
_handler.setFormatter(JsonFormatter())
logger = logging.getLogger("remixx")
logger.handlers = [_handler]
logger.setLevel(logging.INFO)
logger.propagate = False


app = FastAPI(title="Remixx", version="0.1.0")

# CORS so Next.js dev (localhost:3000) can hit FastAPI dev (localhost:8000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def _on_startup() -> None:
    init_db()
    # Preload the catalog DataFrame and retriever so the first /chat request
    # does not pay setup latency.
    await asyncio.to_thread(_catalog)
    await asyncio.to_thread(_retr)


# ── Request / response models ──────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=500)
    persona: str = Field(default="warm")
    k: int = Field(default=5, ge=1, le=20)


class TasteRequest(BaseModel):
    seed_songs: Annotated[
        list[Annotated[str, Field(min_length=1, max_length=120)]],
        Field(min_length=1, max_length=20),
    ]
    persona: str = Field(default="warm")
    k: int = Field(default=8, ge=1, le=20)


class PlaylistRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=500)
    duration_min: int = Field(default=45, ge=10, le=240)
    persona: str = Field(default="warm")


# ── /chat (SSE) ────────────────────────────────────────────────────────────

def _sanitize_song(s: dict) -> dict:
    """Drop pandas-unfriendly types and internal metadata for JSON."""
    out = {}
    for key, val in s.items():
        if isinstance(val, float) and (val != val):  # NaN
            out[key] = None
        elif isinstance(val, (int, float, str, bool)) or val is None:
            out[key] = val
        elif isinstance(val, list):
            out[key] = val
        else:
            out[key] = str(val)
    return out


_SENTINEL = object()


def _run_agent_to_queue(message: str, persona: str, k: int, q: Queue) -> None:
    """Run the (sync) agent generator in a worker thread and push steps onto a queue.

    The agent does CPU/retrieval work, so keep it off the FastAPI event loop.
    """
    try:
        for step in run_agent(message, persona=persona, k=k):
            q.put(("step", step))
    except Exception as exc:  # noqa: BLE001
        q.put(("error", str(exc)))
    finally:
        q.put((_SENTINEL, None))


@app.post("/chat")
async def chat(req: ChatRequest):
    if req.persona not in PERSONAS:
        raise HTTPException(400, f"unknown persona: {req.persona}")
    if is_prompt_injection(req.message):
        logger.info("chat.blocked", {"reason": "prompt_injection", "len": len(req.message)})
        raise HTTPException(400, "request blocked by input guardrail")

    logger.info("chat.start", {"persona": req.persona, "len": len(req.message)})
    t_start = time.time()

    async def event_stream():
        q: Queue = Queue()
        worker = threading.Thread(
            target=_run_agent_to_queue,
            args=(req.message, req.persona, req.k, q),
            daemon=True,
        )
        worker.start()
        loop = asyncio.get_running_loop()
        while True:
            kind, payload = await loop.run_in_executor(None, q.get)
            if kind is _SENTINEL:
                break
            if kind == "error":
                yield {"event": "error", "data": json.dumps({"error": payload})}
                continue
            step = payload
            if step.get("step") == "result":
                conf = compute_confidence(step["picks"])
                data = {
                    "picks": [_sanitize_song(p) for p in step["picks"]],
                    "commentary": step["commentary"],
                    "total_ms": step["total_ms"],
                    "intent": step["intent"],
                    "confidence": conf,
                }
                logger.info("chat.done", {
                    "ms": int((time.time() - t_start) * 1000),
                    "picks": len(step["picks"]),
                    "confidence": conf,
                })
                yield {"event": "result", "data": json.dumps(data)}
            else:
                yield {"event": "step", "data": json.dumps(step)}

    return EventSourceResponse(event_stream())


# ── /taste ────────────────────────────────────────────────────────────────

ARTIST_TASTE_PROFILES: dict[str, dict[str, Any]] = {
    "coldplay": {
        "genre": "alt-rock",
        "mood": "chill",
        "energy": 0.68,
        "valence": 0.62,
        "max_energy": 0.86,
        "likes_acoustic": False,
        "preferred_genres": ["alt-rock", "british", "rock", "pop", "piano", "synth-pop", "indie-pop", "house"],
        "preferred_moods": ["chill", "happy"],
        "excluded_genres": ["r-n-b", "reggaeton", "heavy-metal", "death-metal", "black-metal", "grindcore", "kids", "disney", "comedy"],
        "retrieval_query": "anthemic melodic alt-rock british rock pop piano synth-pop house uplifting bittersweet bright stadium chorus emotional",
        "summary": "Those seeds share Coldplay's center: sky-wide choruses, bright piano/guitar hooks, bittersweet but hopeful emotion, and a polished alt-rock/pop lift.",
    },
    "radiohead": {
        "genre": "alt-rock",
        "mood": "sad",
        "energy": 0.42,
        "valence": 0.28,
        "max_energy": 0.7,
        "likes_acoustic": False,
        "preferred_genres": ["alt-rock", "alternative", "ambient", "idm", "piano", "trip-hop", "british"],
        "preferred_moods": ["sad", "chill"],
        "excluded_genres": ["kids", "disney", "party", "reggaeton", "hardstyle"],
        "retrieval_query": "moody art rock alternative ambient idm piano melancholy uneasy spacious experimental",
        "summary": "Those seeds point to moody art-rock: tense quiet, strange electronics, fragile melody, and a darker emotional floor.",
    },
    "frank ocean": {
        "genre": "r-n-b",
        "mood": "chill",
        "energy": 0.45,
        "valence": 0.42,
        "max_energy": 0.68,
        "likes_acoustic": False,
        "preferred_genres": ["r-n-b", "soul", "indie-pop", "trip-hop", "alternative"],
        "preferred_moods": ["chill", "sad"],
        "excluded_genres": ["hardstyle", "death-metal", "kids", "comedy"],
        "retrieval_query": "left field r-n-b soul intimate nocturnal mellow textured emotional",
        "summary": "Those seeds lean toward intimate left-field R&B: soft edges, emotional negative space, and melody that feels overheard.",
    },
    "billie eilish": {
        "genre": "pop",
        "mood": "sad",
        "energy": 0.34,
        "valence": 0.3,
        "max_energy": 0.6,
        "likes_acoustic": False,
        "preferred_genres": ["pop", "alt-rock", "trip-hop", "ambient", "indie-pop"],
        "preferred_moods": ["sad", "chill"],
        "excluded_genres": ["hardstyle", "party", "kids", "comedy"],
        "retrieval_query": "whisper pop dark bedroom pop minimal bass moody intimate",
        "summary": "Those seeds suggest dark minimal pop: close vocals, heavy quiet, and tension more than volume.",
    },
    "lana del rey": {
        "genre": "singer-songwriter",
        "mood": "sad",
        "energy": 0.32,
        "valence": 0.28,
        "max_energy": 0.58,
        "likes_acoustic": True,
        "preferred_genres": ["singer-songwriter", "piano", "indie-pop", "sad", "romance"],
        "preferred_moods": ["sad", "relaxed", "chill"],
        "excluded_genres": ["hardstyle", "club", "death-metal", "kids"],
        "retrieval_query": "cinematic sad singer songwriter piano romantic slow vintage melancholy",
        "summary": "Those seeds lean cinematic and romantic: slow burn, vintage sadness, soft piano/guitar, and melodrama with restraint.",
    },
    "kendrick lamar": {
        "genre": "hip-hop",
        "mood": "intense",
        "energy": 0.72,
        "valence": 0.45,
        "likes_acoustic": False,
        "preferred_genres": ["hip-hop", "funk", "soul", "jazz", "r-n-b"],
        "preferred_moods": ["intense", "chill"],
        "excluded_genres": ["kids", "disney", "comedy"],
        "retrieval_query": "lyrical hip-hop jazz funk sharp drums intense thoughtful groove",
        "summary": "Those seeds read as lyrical, rhythm-forward hip-hop: sharp drums, dense writing, and a serious emotional charge.",
    },
}

def _taste_blocking(seed_songs: list[str], persona: str, k: int) -> dict:
    """All the profile + RAG work for /taste, run on a worker thread."""
    t0 = time.time()
    query = ", ".join(seed_songs)
    retr = _retr()
    df = _catalog()
    seed_profile = _infer_seed_profile(seed_songs)
    retrieval_query = seed_profile.get("retrieval_query", query)
    hits = retr.search(retrieval_query, k=80)
    candidates = []
    seen_candidate_ids: set[str] = set()
    for h in hits:
        row = df[df["id"] == h["id"]]
        if len(row):
            candidate = {**row.iloc[0].to_dict(), "_rag_score": h["score"]}
            candidates.append(candidate)
            seen_candidate_ids.add(str(candidate.get("id")))

    for artist in seed_profile.get("preferred_artists", []):
        artist_rows = df[df["artist"].str.contains(artist, case=False, na=False)]
        for _, row in artist_rows.iterrows():
            if str(row["id"]) in seen_candidate_ids:
                continue
            candidates.append({**row.to_dict(), "_rag_score": 0.35, "_seed_artist_match": True})
            seen_candidate_ids.add(str(row["id"]))

    profile = _infer_taste_profile(seed_songs, candidates, seed_profile)
    user_prefs = {
        "genre": profile.get("genre", "pop"),
        "mood": profile.get("mood", "chill"),
        "energy": float(profile.get("energy", 0.5)),
        "valence": float(profile.get("valence", profile.get("energy", 0.5))),
        "likes_acoustic": bool(profile.get("likes_acoustic", False)),
        "preferred_genres": profile.get("preferred_genres", []),
        "preferred_moods": profile.get("preferred_moods", []),
        "preferred_artists": profile.get("preferred_artists", []),
        "excluded_genres": set(profile.get("excluded_genres", [])),
    }
    if "max_energy" in profile:
        user_prefs["max_energy"] = float(profile["max_energy"])
    mood = str(user_prefs["mood"]).lower()
    if mood in {"melancholic", "melancholy", "moody", "brooding", "dark"}:
        user_prefs["mood"] = "sad"
    elif mood in {"soft", "calm", "gentle"}:
        user_prefs["mood"] = "relaxed"
    if float(user_prefs["energy"]) <= 0.45:
        user_prefs.setdefault("max_energy", 0.6)
        user_prefs.setdefault("excluded_genres", set())
        user_prefs["excluded_genres"].update({
            "black-metal",
            "club",
            "death-metal",
            "drum-and-bass",
            "dubstep",
            "electro",
            "hard-rock",
            "hardstyle",
            "progressive-house",
            "trance",
        })
    user_prefs.update(infer_query_overrides(query))
    ranked = rerank(user_prefs, candidates, k=k)
    comm = taste_commentary(persona, seed_songs, profile, ranked)

    return {
        "profile": profile,
        "picks": [_sanitize_song(p) for p in ranked],
        "commentary": comm,
        "confidence": compute_confidence(ranked),
        "ms": int((time.time() - t0) * 1000),
    }


def _infer_seed_profile(seed_songs: list[str]) -> dict:
    parsed = [_parse_seed(seed) for seed in seed_songs]
    artists = [artist.lower() for _, artist in parsed if artist]
    titles = [title.lower() for title, _ in parsed if title]

    for artist, profile in ARTIST_TASTE_PROFILES.items():
        if any(artist in seed_artist for seed_artist in artists):
            return {**profile, "preferred_artists": [artist]}

    if any("rain" in title for title in titles):
        return {
            "mood": "sad",
            "energy": 0.25,
            "valence": 0.2,
            "likes_acoustic": True,
            "preferred_genres": ["piano", "classical", "new-age", "ambient"],
            "preferred_moods": ["sad", "relaxed", "chill"],
            "retrieval_query": "piano ambient new-age sad relaxed gentle rain instrumental",
        }

    joined = " ".join([*titles, *artists])
    if any(word in joined for word in ["sad", "blue", "tears", "hurt", "lonely", "heartbreak"]):
        return {
            "genre": "singer-songwriter",
            "mood": "sad",
            "energy": 0.35,
            "valence": 0.28,
            "max_energy": 0.62,
            "likes_acoustic": True,
            "preferred_genres": ["singer-songwriter", "piano", "indie-pop", "soul", "sad"],
            "preferred_moods": ["sad", "relaxed", "chill"],
            "retrieval_query": f"{joined} sad singer songwriter piano mellow acoustic emotional",
            "summary": "The seeds point toward a sad, intimate profile: lower energy, exposed melody, and emotional lyrics over flash.",
        }
    if any(word in joined for word in ["dance", "stars", "party", "night", "lights", "alive"]):
        return {
            "genre": "dance",
            "mood": "happy",
            "energy": 0.72,
            "valence": 0.7,
            "likes_acoustic": False,
            "preferred_genres": ["dance", "house", "edm", "synth-pop", "pop"],
            "preferred_moods": ["happy", "chill"],
            "retrieval_query": f"{joined} bright dance pop synth house uplifting chorus",
            "summary": "The seeds point toward bright dance-pop lift: glossy rhythm, open choruses, and high-valence momentum.",
        }

    return {}


def _parse_seed(seed: str) -> tuple[str, str]:
    cleaned = seed.strip()
    if " - " in cleaned:
        title, artist = cleaned.rsplit(" - ", 1)
    elif " by " in cleaned.lower():
        parts = cleaned.rsplit(" by ", 1)
        title, artist = parts[0], parts[1]
    else:
        title, artist = cleaned, ""
    return title.strip(), artist.strip()


def _infer_taste_profile(seed_songs: list[str], candidates: list[dict], seed_profile: dict | None = None) -> dict:
    seed_profile = seed_profile or {}
    top = candidates[:12]
    if seed_profile:
        genre = seed_profile.get("genre", "pop")
        mood = seed_profile.get("mood", "chill")
        energy = float(seed_profile.get("energy", 0.5))
        valence = float(seed_profile.get("valence", energy))
        acousticness = 0.7 if seed_profile.get("likes_acoustic") else 0.0
        max_energy = seed_profile.get("max_energy")
    elif top:
        genre = pd.Series([c.get("genre", "pop") for c in top]).mode().iloc[0]
        mood = pd.Series([c.get("mood", "chill") for c in top]).mode().iloc[0]
        energy = float(pd.Series([float(c.get("energy", 0.5) or 0.5) for c in top]).mean())
        valence = float(pd.Series([float(c.get("valence", energy) or energy) for c in top]).mean())
        acousticness = float(pd.Series([float(c.get("acousticness", 0) or 0) for c in top]).mean())
        max_energy = None
    else:
        genre = "pop"
        mood = "chill"
        energy = 0.5
        valence = 0.5
        acousticness = 0.0
        max_energy = None

    names = ", ".join(seed_songs[:3])
    energy_word = "low-energy" if energy < 0.45 else "mid-tempo" if energy < 0.7 else "high-energy"
    summary = seed_profile.get("summary") or (
        f"Your seeds point toward {energy_word} {genre} with a {mood} tilt. "
        f"Remixx is matching the shared texture from {names}, then reranking for nearby mood, energy, and acoustic balance."
    )
    return {
        "genre": str(genre),
        "mood": str(mood),
        "energy": round(energy, 2),
        "valence": round(valence, 2),
        **({"max_energy": max_energy} if max_energy is not None else {}),
        "likes_acoustic": acousticness > 0.5,
        "preferred_genres": seed_profile.get("preferred_genres", []),
        "preferred_moods": seed_profile.get("preferred_moods", []),
        "preferred_artists": seed_profile.get("preferred_artists", []),
        "excluded_genres": seed_profile.get("excluded_genres", []),
        "summary": summary,
    }


@app.post("/taste")
async def taste(req: TasteRequest):
    if req.persona not in PERSONAS:
        raise HTTPException(400, f"unknown persona: {req.persona}")
    joined = ", ".join(req.seed_songs)
    if is_prompt_injection(joined):
        logger.info("taste.blocked", {"reason": "prompt_injection"})
        raise HTTPException(400, "request blocked by input guardrail")
    try:
        return await asyncio.to_thread(
            _taste_blocking, req.seed_songs, req.persona, req.k
        )
    except ValueError as e:
        raise HTTPException(500, str(e))


# ── /playlist ──────────────────────────────────────────────────────────────

def _arc_label(i: int, total: int) -> str:
    """Map track index to a narrative arc segment."""
    if total <= 0:
        return "opening"
    pos = i / max(total - 1, 1)
    if pos < 0.25: return "opening"
    if pos < 0.6:  return "build"
    if pos < 0.85: return "peak"
    return "wind-down"


def _playlist_blocking(prompt: str, persona: str, duration_min: int) -> dict:
    """Run the agent and tag arc positions."""
    # rough rule: ~3 min per track average
    k = max(8, min(15, duration_min // 4))

    t0 = time.time()
    final_step = None
    for step in run_agent(prompt, persona=persona, k=k):
        if step.get("step") == "result":
            final_step = step
            break

    if not final_step:
        raise RuntimeError("agent produced no result")

    picks = final_step["picks"]
    for i, p in enumerate(picks):
        p["_arc"] = _arc_label(i, len(picks))

    return {
        "prompt": prompt,
        "duration_min": duration_min,
        "picks": [_sanitize_song(p) for p in picks],
        "commentary": final_step["commentary"],
        "intent": final_step["intent"],
        "confidence": compute_confidence(picks),
        "ms": int((time.time() - t0) * 1000),
    }


@app.post("/playlist")
async def playlist(req: PlaylistRequest):
    if req.persona not in PERSONAS:
        raise HTTPException(400, f"unknown persona: {req.persona}")
    if is_prompt_injection(req.prompt):
        logger.info("playlist.blocked", {"reason": "prompt_injection", "len": len(req.prompt)})
        raise HTTPException(400, "request blocked by input guardrail")
    try:
        return await asyncio.to_thread(
            _playlist_blocking, req.prompt, req.persona, req.duration_min
        )
    except RuntimeError as e:
        raise HTTPException(500, str(e))


# ── /personas ──────────────────────────────────────────────────────────────

@app.get("/personas")
async def list_personas():
    return [
        {"key": k, "name": v["name"], "tagline": v["tagline"]}
        for k, v in PERSONAS.items()
    ]


# ── /catalog/{id} ──────────────────────────────────────────────────────────

@app.get("/catalog/{track_id}")
async def get_track(track_id: str):
    df = _catalog()
    row = df[df["id"] == track_id]
    if len(row) == 0:
        raise HTTPException(404, f"track {track_id} not found")
    return _sanitize_song(row.iloc[0].to_dict())


# ── /sessions, /playlists ──────────────────────────────────────────────────

class SavePlaylistRequest(BaseModel):
    session_id: str | None = None
    name: Annotated[str, Field(min_length=1, max_length=120)]
    prompt: str | None = Field(default=None, max_length=500)
    tracks: list[dict]


@app.post("/sessions")
async def new_session():
    return {"id": create_session()}


@app.post("/playlists")
async def save_playlist_endpoint(req: SavePlaylistRequest):
    pid = save_playlist(req.session_id, req.name, req.prompt, req.tracks)
    return {"id": pid}


@app.get("/playlists")
async def list_playlists_endpoint(session_id: str | None = None, limit: int = 50):
    return list_playlists(session_id=session_id, limit=min(max(limit, 1), 200))


# ── /healthz ───────────────────────────────────────────────────────────────

@app.get("/healthz")
async def healthz():
    return {"ok": True, "catalog_size": len(_catalog()), "personas": list(PERSONAS.keys())}
