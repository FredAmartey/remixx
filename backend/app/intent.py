"""Fast intent classifier: chat | playlist | taste.

The first implementation used a Haiku call for every request, which made the UI
feel broken during demos. These rules cover the app's visible workflows without
leaving the request path waiting on an LLM.
"""
from __future__ import annotations

import re
from typing import Literal, TypedDict


class Intent(TypedDict):
    mode: Literal["chat", "playlist", "taste"]
    duration_min: int | None
    seed_songs: list[str]


DURATION_RE = re.compile(r"\b(\d{1,3})\s*(?:min|mins|minute|minutes)\b", re.I)
HOUR_RE = re.compile(r"\b(\d(?:\.\d+)?)\s*(?:hour|hours|hr|hrs)\b", re.I)
SONG_SPLIT_RE = re.compile(r"\s*(?:,|\n|;)\s*")
SONG_PAIR_RE = re.compile(r"\S+\s+(?:—|-|by)\s+\S+", re.I)


def _duration_minutes(message: str) -> int | None:
    minute_match = DURATION_RE.search(message)
    if minute_match:
        return int(minute_match.group(1))

    hour_match = HOUR_RE.search(message)
    if hour_match:
        return int(float(hour_match.group(1)) * 60)

    return None


def _seed_songs(message: str) -> list[str]:
    cleaned = re.sub(r"^(?:here are|i love|songs i love|my favorites are)[:\s]+", "", message, flags=re.I)
    parts = [part.strip(" .") for part in SONG_SPLIT_RE.split(cleaned) if part.strip(" .")]
    return [part for part in parts if SONG_PAIR_RE.search(part)]


def classify_intent(message: str) -> Intent:
    msg = message.strip()
    lower = msg.lower()
    duration_min = _duration_minutes(msg)
    seed_songs = _seed_songs(msg)

    if len(seed_songs) >= 3:
        return {"mode": "taste", "duration_min": None, "seed_songs": seed_songs}

    if duration_min is not None or any(
        word in lower for word in ("playlist", "mix for", "build me", "make me")
    ):
        return {
            "mode": "playlist",
            "duration_min": duration_min,
            "seed_songs": [],
        }

    return {"mode": "chat", "duration_min": None, "seed_songs": []}
