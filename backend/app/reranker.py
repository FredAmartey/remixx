"""Deterministic weighted-feature scorer, ported from the Module 3 recommender.

Weights:
- Genre match: +2.0
- Mood match: +1.5
- Energy proximity: up to +1.0 (closer = higher)
- Valence fit: up to +0.5
- Danceability: up to +0.3
- Acoustic preference: +0.5 if user likes acoustic AND track is acoustic; +0.3 if not-acoustic match.

Used as a deterministic re-rank pass on top of the RAG candidate list, and as a
transparent confidence breakdown for each recommendation.
"""
from __future__ import annotations

from typing import Any


def score_song(user_prefs: dict[str, Any], song: dict[str, Any]) -> tuple[float, list[str]]:
    """Score one song against a user profile. Returns (score, list of reason strings)."""
    score = 0.0
    reasons: list[str] = []

    if str(song.get("genre", "")).lower() == str(user_prefs.get("genre", "")).lower():
        score += 2.0
        reasons.append(f"genre match: {song['genre']} (+2.0)")

    if str(song.get("mood", "")).lower() == str(user_prefs.get("mood", "")).lower():
        score += 1.5
        reasons.append(f"mood match: {song['mood']} (+1.5)")

    if "energy" in user_prefs and "energy" in song:
        gap = abs(float(song["energy"]) - float(user_prefs["energy"]))
        proximity = round(1.0 - gap, 2)
        score += proximity
        reasons.append(f"energy proximity: {proximity:.2f}")

    if "energy" in user_prefs and "valence" in song:
        valence_score = round(0.5 * (1.0 - abs(float(song["valence"]) - float(user_prefs["energy"]))), 2)
        score += valence_score
        reasons.append(f"valence fit: +{valence_score:.2f}")

    if "danceability" in song:
        dance_score = round(0.3 * float(song["danceability"]), 2)
        score += dance_score
        reasons.append(f"danceability: +{dance_score:.2f}")

    if user_prefs.get("likes_acoustic") and float(song.get("acousticness", 0)) > 0.7:
        score += 0.5
        reasons.append("acoustic match (+0.5)")
    elif not user_prefs.get("likes_acoustic") and float(song.get("acousticness", 0)) < 0.3:
        score += 0.3
        reasons.append("non-acoustic fit (+0.3)")

    return round(score, 2), reasons


def rerank(
    user_prefs: dict[str, Any],
    candidates: list[dict[str, Any]],
    k: int,
) -> list[dict[str, Any]]:
    """Score every candidate and return the top-k with `_score` and `_reasons` attached."""
    scored: list[dict[str, Any]] = []
    for song in candidates:
        s, r = score_song(user_prefs, song)
        scored.append({**song, "_score": s, "_reasons": r})
    scored.sort(key=lambda x: x["_score"], reverse=True)
    return scored[:k]
