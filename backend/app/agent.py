"""Observable agent loop: plan → retrieve → rerank → self-critique → reorder → commentary.

Each step yielded as {step, title, detail, ms} so the frontend can show the reasoning chain.
The final yield is {step: "result", picks, commentary, total_ms, intent}.

This is the substantive AI feature: ties RAG + reranker + a critique pass together.
"""
from __future__ import annotations

import json
import time
from typing import Generator

import pandas as pd

from app.guardrails import extract_first_json
from app.intent import classify_intent
from app.llm import LLMClient
from app.personas import commentary as persona_commentary
from app.rag import CATALOG, RAGRetriever
from app.reranker import rerank

_catalog_df: pd.DataFrame | None = None
_retriever: RAGRetriever | None = None


def _catalog() -> pd.DataFrame:
    global _catalog_df
    if _catalog_df is None:
        _catalog_df = pd.read_csv(CATALOG)
    return _catalog_df


def _retr() -> RAGRetriever:
    global _retriever
    if _retriever is None:
        _retriever = RAGRetriever.load()
    return _retriever


CRITIQUE_SYSTEM = (
    "You are a quality-control reviewer for music recommendations. "
    "You look at a ranked list of picks and identify ones that obviously don't match the user's intent. "
    "Reply with strict JSON only:\n"
    '{"issues": [{"index": <int>, "reason": "<short>"}], "reorder": null | [<int>, ...]}\n\n'
    "Indexes are 1-based and must be within [1, k] where k is the number of picks shown. "
    "Do not include duplicate indexes in `reorder`. "
    "If everything fits, return {\"issues\": [], \"reorder\": null}. "
    "Be conservative — only flag obvious mismatches, not subjective preferences."
)


def _critique_prompt(user_query: str, picks: list[dict]) -> str:
    pick_str = "\n".join(
        f"{i+1}. {p.get('title')} — {p.get('artist')} "
        f"(genre: {p.get('genre')}, mood: {p.get('mood')}, energy: {float(p.get('energy', 0)):.2f})"
        for i, p in enumerate(picks)
    )
    return f"User wanted: {user_query}\n\nPicks ranked so far:\n{pick_str}\n\nReply with the JSON."


def run_agent(
    user_query: str,
    persona: str = "warm",
    k: int = 5,
) -> Generator[dict, None, None]:
    """Yield observable steps and finally a result dict."""
    t0 = time.time()
    df = _catalog()
    retr = _retr()
    llm = LLMClient()

    # Step 1: parse intent
    t = time.time()
    intent = classify_intent(user_query)
    yield {
        "step": 1,
        "title": "Parse intent",
        "detail": f"mode={intent['mode']}",
        "ms": int((time.time() - t) * 1000),
    }

    # Mode-aware adjustments
    mode = intent.get("mode", "chat")
    seed_songs = intent.get("seed_songs", []) or []
    duration_min = intent.get("duration_min")

    # For taste mode, use seed songs as the retrieval query
    retrieval_query = ", ".join(seed_songs) if mode == "taste" and seed_songs else user_query

    # For playlist mode, bump k based on duration (~3-4 min per track)
    if mode == "playlist" and duration_min:
        k = max(5, min(12, duration_min // 4))

    # Step 2: retrieve
    t = time.time()
    hits = retr.search(retrieval_query, k=30)
    candidates: list[dict] = []
    for h in hits:
        row = df[df["id"] == h["id"]]
        if len(row):
            candidates.append({**row.iloc[0].to_dict(), "_rag_score": h["score"]})
    yield {
        "step": 2,
        "title": "Retrieve candidates",
        "detail": f"{len(candidates)} via semantic search",
        "ms": int((time.time() - t) * 1000),
    }

    if not candidates:
        yield {"step": "result", "picks": [], "commentary": "No catalog matches found.", "total_ms": int((time.time() - t0) * 1000), "intent": intent}
        return

    # Step 3: derive user prefs from top retrievals + rerank
    t = time.time()
    top_genres = pd.Series([c["genre"] for c in candidates[:10]]).mode()
    top_moods = pd.Series([c["mood"] for c in candidates[:10]]).mode()
    user_prefs = {
        "genre": top_genres.iloc[0] if len(top_genres) else "pop",
        "mood": top_moods.iloc[0] if len(top_moods) else "chill",
        "energy": float(pd.Series([c["energy"] for c in candidates[:10]]).mean()),
        "likes_acoustic": float(pd.Series([c["acousticness"] for c in candidates[:10]]).mean()) > 0.5,
    }
    ranked = rerank(user_prefs, candidates, k=k * 2)
    yield {
        "step": 3,
        "title": "Rerank with weighted scorer",
        "detail": f"top {min(len(ranked), k * 2)} by score; derived prefs: {user_prefs['genre']}/{user_prefs['mood']}",
        "ms": int((time.time() - t) * 1000),
    }

    # Step 4: self-critique
    t = time.time()
    crit_raw = llm.complete(
        "sonnet",
        _critique_prompt(user_query, ranked[:k]),
        max_tokens=600,
        system=CRITIQUE_SYSTEM,
    )
    text = extract_first_json(crit_raw)
    crit: dict = {"issues": [], "reorder": None}
    if text:
        try:
            crit = json.loads(text)
        except json.JSONDecodeError:
            pass
    issue_count = len(crit.get("issues", []))
    yield {
        "step": 4,
        "title": "Self-critique",
        "detail": f"{issue_count} issue(s) found",
        "ms": int((time.time() - t) * 1000),
    }

    # Step 5: apply reorder
    t = time.time()
    final = ranked[:k]
    reorder = crit.get("reorder")
    if reorder and isinstance(reorder, list):
        try:
            seen_ids: set[str] = set()
            deduped: list[dict] = []
            for i in reorder:
                if not (isinstance(i, int) and 1 <= i <= k):
                    continue
                candidate = ranked[i - 1]
                cid = candidate.get("id")
                if cid in seen_ids:
                    continue
                seen_ids.add(cid)
                deduped.append(candidate)
                if len(deduped) >= k:
                    break
            if deduped:
                final = deduped
                if len(final) < k:
                    # backfill from ranked, skipping ones already chosen
                    for r in ranked:
                        if r.get("id") not in seen_ids:
                            final.append(r)
                            seen_ids.add(r.get("id"))
                            if len(final) >= k:
                                break
        except (IndexError, ValueError, TypeError):
            final = ranked[:k]
    yield {
        "step": 5,
        "title": "Reorder & finalize",
        "detail": f"{len(final)} picks",
        "ms": int((time.time() - t) * 1000),
    }

    # Playlist mode: tag each pick with a narrative arc segment
    if mode == "playlist":
        for i, p in enumerate(final):
            pos = i / max(len(final) - 1, 1)
            if pos < 0.25:
                p["_arc"] = "opening"
            elif pos < 0.6:
                p["_arc"] = "build"
            elif pos < 0.85:
                p["_arc"] = "peak"
            else:
                p["_arc"] = "wind-down"

    # Step 6: persona commentary
    t = time.time()
    comm = persona_commentary(persona, user_query, final)
    yield {
        "step": 6,
        "title": "DJ commentary",
        "detail": f"{len(comm)} chars in {persona} voice",
        "ms": int((time.time() - t) * 1000),
    }

    yield {
        "step": "result",
        "picks": final,
        "commentary": comm,
        "total_ms": int((time.time() - t0) * 1000),
        "intent": intent,
    }
