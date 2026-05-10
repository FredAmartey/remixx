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


HIGH_ENERGY_GENRES = {
    "black-metal",
    "club",
    "drum-and-bass",
    "dubstep",
    "electro",
    "death-metal",
    "hard-rock",
    "hardstyle",
    "progressive-house",
    "trance",
}


def infer_query_overrides(query: str) -> dict[str, Any]:
    """Small deterministic guardrail for vibe words the catalog often misreads."""
    q = query.lower()
    overrides: dict[str, Any] = {}

    if any(w in q for w in ["slow", "slower", "gentle", "soft", "quiet", "calm", "breathe", "breath"]):
        overrides.update({"mood": "relaxed", "energy": 0.35, "max_energy": 0.55})

    if any(w in q for w in ["late night", "late-night", "night", "nocturnal", "rain", "rainy", "drive", "drives"]):
        overrides.setdefault("mood", "chill")
        overrides.setdefault("energy", 0.42)
        overrides.setdefault("max_energy", 0.65)

    if any(w in q for w in ["focus", "study", "work", "concentrate"]):
        overrides.update({"mood": "chill", "energy": 0.32, "max_energy": 0.58})

    if any(
        w in q
        for w in [
            "no sharp edges",
            "soft edges",
            "low distraction",
            "deep focus",
            "steady momentum",
        ]
    ):
        overrides.update({"mood": "chill", "energy": 0.34, "max_energy": 0.55})

    if any(w in q for w in ["party", "hype", "workout", "gym", "festival", "intense"]):
        overrides.update({"mood": "intense", "energy": 0.82})
        overrides.pop("max_energy", None)

    if "max_energy" in overrides:
        overrides["excluded_genres"] = HIGH_ENERGY_GENRES

    return overrides


def score_song(user_prefs: dict[str, Any], song: dict[str, Any]) -> tuple[float, list[str]]:
    """Score one song against a user profile. Returns (score, list of reason strings)."""
    score = 0.0
    reasons: list[str] = []

    genre = str(song.get("genre", "")).lower()
    artist = str(song.get("artist", "")).lower()
    preferred_artists = {
        str(a).lower() for a in user_prefs.get("preferred_artists", [])
    }
    if any(preferred in artist for preferred in preferred_artists):
        score += 2.4
        reasons.append("seed artist match (+2.4)")

    preferred_genres = {
        str(g).lower() for g in user_prefs.get("preferred_genres", [])
    }
    if genre == str(user_prefs.get("genre", "")).lower():
        score += 2.0
        reasons.append(f"genre match: {song['genre']} (+2.0)")
    elif genre in preferred_genres:
        score += 1.4
        reasons.append(f"related genre: {song['genre']} (+1.4)")

    mood = str(song.get("mood", "")).lower()
    preferred_moods = {str(m).lower() for m in user_prefs.get("preferred_moods", [])}
    if mood == str(user_prefs.get("mood", "")).lower():
        score += 1.5
        reasons.append(f"mood match: {song['mood']} (+1.5)")
    elif mood in preferred_moods:
        score += 0.9
        reasons.append(f"related mood: {song['mood']} (+0.9)")

    if "energy" in user_prefs and "energy" in song:
        gap = abs(float(song["energy"]) - float(user_prefs["energy"]))
        proximity = round(1.0 - gap, 2)
        score += proximity
        reasons.append(f"energy proximity: {proximity:.2f}")

    if "max_energy" in user_prefs and "energy" in song:
        energy = float(song["energy"])
        max_energy = float(user_prefs["max_energy"])
        if energy > max_energy:
            penalty = round((energy - max_energy) * 3.0, 2)
            score -= penalty
            reasons.append(f"too energetic: -{penalty:.2f}")

    excluded_genres = {str(g).lower() for g in user_prefs.get("excluded_genres", set())}
    if genre in excluded_genres:
        score -= 2.25
        reasons.append("genre guardrail: -2.25")

    if "energy" in user_prefs and "valence" in song:
        target_valence = float(user_prefs.get("valence", user_prefs["energy"]))
        valence_score = round(0.5 * (1.0 - abs(float(song["valence"]) - target_valence)), 2)
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

    if "_rag_score" in song:
        retrieval_bonus = round(min(max(float(song.get("_rag_score", 0.0)), 0.0), 0.25) * 4.0, 2)
        if retrieval_bonus:
            score += retrieval_bonus
            reasons.append(f"retrieval match: +{retrieval_bonus:.2f}")

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
