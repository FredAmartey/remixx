"""Observable agent loop: plan → retrieve → rerank → critique → finalize → commentary.

Each step yielded as {step, title, detail, ms} so the frontend can show the reasoning chain.
The final yield is {step: "result", picks, commentary, total_ms, intent}.

This is the substantive AI feature: ties RAG + reranker + a critique pass together.
"""
from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor
from typing import Generator

import pandas as pd

from app.intent import classify_intent
from app.personas import commentary as persona_commentary
from app.rag import CATALOG, RAGRetriever
from app.reranker import infer_query_overrides, rerank

_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="remixx-agent")

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


def _critique_picks(user_prefs: dict, picks: list[dict]) -> dict:
    """Fast deterministic QC pass that flags obvious energy/genre mismatches."""
    issues = []
    max_energy = user_prefs.get("max_energy")
    excluded_genres = {str(g).lower() for g in user_prefs.get("excluded_genres", set())}

    for index, pick in enumerate(picks, start=1):
        energy = float(pick.get("energy", 0) or 0)
        genre = str(pick.get("genre", "")).lower()
        if max_energy is not None and energy > float(max_energy):
            issues.append({"index": index, "reason": "too energetic for request"})
        elif genre in excluded_genres:
            issues.append({"index": index, "reason": "genre conflicts with vibe guardrail"})

    issue_indexes = {issue["index"] for issue in issues}
    reorder = [
        *[i for i in range(1, len(picks) + 1) if i not in issue_indexes],
        *[i for i in range(1, len(picks) + 1) if i in issue_indexes],
    ]
    return {"issues": issues, "reorder": reorder if issues else None}


def run_agent(
    user_query: str,
    persona: str = "warm",
    k: int = 5,
) -> Generator[dict, None, None]:
    """Yield observable steps and finally a result dict."""
    t0 = time.time()
    df = _catalog()
    retr = _retr()

    # Steps 1 + 2 in parallel — intent and retrieval are independent.
    t = time.time()
    intent_fut = _executor.submit(classify_intent, user_query)
    retrieve_fut = _executor.submit(retr.search, user_query, 60)

    intent = intent_fut.result()
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

    # For taste mode, use seed songs as the retrieval query — but we already kicked off
    # retrieval with user_query. Re-run if needed.
    if mode == "taste" and seed_songs:
        retrieve_fut.cancel()
        retrieval_query = ", ".join(seed_songs)
        hits = retr.search(retrieval_query, k=60)
    else:
        hits = retrieve_fut.result()

    # For playlist mode, bump k based on duration (~3-4 min per track)
    if mode == "playlist" and duration_min:
        k = max(5, min(12, duration_min // 4))

    t2 = time.time()
    candidates: list[dict] = []
    for h in hits:
        row = df[df["id"] == h["id"]]
        if len(row):
            candidates.append({**row.iloc[0].to_dict(), "_rag_score": h["score"]})
    yield {
        "step": 2,
        "title": "Retrieve candidates",
        "detail": f"{len(candidates)} via catalog retrieval",
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
    user_prefs.update(infer_query_overrides(user_query))
    ranked = rerank(user_prefs, candidates, k=k * 2)
    yield {
        "step": 3,
        "title": "Rerank with weighted scorer",
        "detail": f"top {min(len(ranked), k * 2)} by score; derived prefs: {user_prefs['genre']}/{user_prefs['mood']}",
        "ms": int((time.time() - t) * 1000),
    }

    # Step 4: self-critique
    t = time.time()
    crit = _critique_picks(user_prefs, ranked[:k])
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
