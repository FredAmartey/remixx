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
import re
import threading
import time
from pathlib import Path
from queue import Queue
from typing import Any

import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

from app.agent import run_agent, _catalog, _retr
from app.llm import LLMClient
from app.personas import PERSONAS, commentary as persona_commentary
from app.rag import CATALOG
from app.reranker import rerank


app = FastAPI(title="Remixx", version="0.1.0")

# CORS so Next.js dev (localhost:3000) can hit FastAPI dev (localhost:8000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request / response models ──────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=500)
    persona: str = Field(default="warm")
    k: int = Field(default=5, ge=1, le=20)


class TasteRequest(BaseModel):
    seed_songs: list[str] = Field(min_length=1, max_length=20)
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

    The agent transitively calls asyncio.run() inside LLMClient — we cannot let
    that happen on the FastAPI event loop, so we isolate it on a thread.
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
                data = {
                    "picks": [_sanitize_song(p) for p in step["picks"]],
                    "commentary": step["commentary"],
                    "total_ms": step["total_ms"],
                    "intent": step["intent"],
                }
                yield {"event": "result", "data": json.dumps(data)}
            else:
                yield {"event": "step", "data": json.dumps(step)}

    return EventSourceResponse(event_stream())


# ── /taste ────────────────────────────────────────────────────────────────

PROFILE_SYSTEM = (
    "You analyze a list of songs a user loves and infer their taste profile. "
    "Reply with strict JSON only:\n"
    '{"genre": "<one>", "mood": "<one>", "energy": <0..1>, "likes_acoustic": <bool>, "summary": "<2 sentences>"}\n'
    "Use lowercase genre/mood. The summary should sound like a music critic — specific and evocative."
)


def _taste_blocking(seed_songs: list[str], persona: str, k: int) -> dict:
    """All the LLM + RAG work for /taste, run on a worker thread."""
    t0 = time.time()
    llm = LLMClient()
    seed_str = "\n".join(f"- {s}" for s in seed_songs)
    raw = llm.complete(
        "sonnet",
        f"Songs the user loves:\n{seed_str}\n\nReply with the JSON profile.",
        system=PROFILE_SYSTEM,
        max_tokens=500,
    )
    m = re.search(r"\{.*\}", raw, re.DOTALL)
    if not m:
        raise ValueError("could not parse taste profile")
    try:
        profile = json.loads(m.group())
    except json.JSONDecodeError as e:
        raise ValueError(f"invalid taste profile JSON: {e}") from e

    query = ", ".join(seed_songs)
    retr = _retr()
    df = _catalog()
    hits = retr.search(query, k=30)
    candidates = []
    for h in hits:
        row = df[df["id"] == h["id"]]
        if len(row):
            candidates.append({**row.iloc[0].to_dict(), "_rag_score": h["score"]})

    user_prefs = {
        "genre": profile.get("genre", "pop"),
        "mood": profile.get("mood", "chill"),
        "energy": float(profile.get("energy", 0.5)),
        "likes_acoustic": bool(profile.get("likes_acoustic", False)),
    }
    ranked = rerank(user_prefs, candidates, k=k)
    comm = persona_commentary(persona, f"music similar to: {query}", ranked)

    return {
        "profile": profile,
        "picks": [_sanitize_song(p) for p in ranked],
        "commentary": comm,
        "ms": int((time.time() - t0) * 1000),
    }


@app.post("/taste")
async def taste(req: TasteRequest):
    if req.persona not in PERSONAS:
        raise HTTPException(400, f"unknown persona: {req.persona}")
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
    """Run the agent and tag arc positions. Worker thread because of asyncio.run inside."""
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
        "ms": int((time.time() - t0) * 1000),
    }


@app.post("/playlist")
async def playlist(req: PlaylistRequest):
    if req.persona not in PERSONAS:
        raise HTTPException(400, f"unknown persona: {req.persona}")
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


# ── /healthz ───────────────────────────────────────────────────────────────

@app.get("/healthz")
async def healthz():
    return {"ok": True, "catalog_size": len(_catalog()), "personas": list(PERSONAS.keys())}
