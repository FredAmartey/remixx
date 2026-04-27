"""Intent classifier: chat | playlist | taste.

Uses Haiku with a JSON-output system prompt. Falls back to "chat" on parse errors.
"""
from __future__ import annotations

import json
import re
from typing import Literal, TypedDict

from app.llm import LLMClient


class Intent(TypedDict):
    mode: Literal["chat", "playlist", "taste"]
    duration_min: int | None
    seed_songs: list[str]


SYSTEM = """You classify user messages for Remixx, a music app. Reply with strict JSON only — no markdown, no commentary:

{"mode": "chat" | "playlist" | "taste", "duration_min": null | <int>, "seed_songs": []}

Rules:
- "playlist" if the user asks for a playlist OR names a duration (minutes/hours)
- "taste" if the user lists 3+ songs/artists they like (with — or "by" or "—" between artist and title)
- "chat" otherwise (a single song request, a vibe description, or a general question)

When mode is "playlist" and a duration is named, set duration_min. Otherwise null.
When mode is "taste", populate seed_songs with the song strings as written.
"""


def classify_intent(message: str) -> Intent:
    client = LLMClient()
    raw = client.complete("haiku", message, max_tokens=300, system=SYSTEM)
    match = re.search(r'\{.*?\}', raw, re.DOTALL)
    if not match:
        return {"mode": "chat", "duration_min": None, "seed_songs": []}
    try:
        parsed = json.loads(match.group())
        return {
            "mode": parsed.get("mode", "chat") if parsed.get("mode") in {"chat", "playlist", "taste"} else "chat",
            "duration_min": parsed.get("duration_min"),
            "seed_songs": parsed.get("seed_songs", []),
        }
    except json.JSONDecodeError:
        return {"mode": "chat", "duration_min": None, "seed_songs": []}
