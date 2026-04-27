"""Thin SQLite layer for Remixx sessions, messages, and saved playlists.

Single-file DB at backend/data/remixx.db. Schema is created on first import via
init_db(). All queries use the stdlib sqlite3 with row_factory=dict-style access.
"""
from __future__ import annotations

import json
import sqlite3
import time
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

DB_PATH = Path(__file__).resolve().parents[1] / "data" / "remixx.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    created_at INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    ts INTEGER NOT NULL,
    FOREIGN KEY(session_id) REFERENCES sessions(id)
);

CREATE TABLE IF NOT EXISTS playlists (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT,
    name TEXT NOT NULL,
    prompt TEXT,
    tracks_json TEXT NOT NULL,
    created_at INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id, ts);
CREATE INDEX IF NOT EXISTS idx_playlists_session ON playlists(session_id, created_at DESC);
"""


def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with _conn() as c:
        c.executescript(SCHEMA)


@contextmanager
def _conn() -> Iterator[sqlite3.Connection]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def _now_ms() -> int:
    return int(time.time() * 1000)


def create_session() -> str:
    sid = uuid.uuid4().hex
    with _conn() as c:
        c.execute("INSERT INTO sessions (id, created_at) VALUES (?, ?)", (sid, _now_ms()))
    return sid


def add_message(session_id: str, role: str, content: str) -> None:
    with _conn() as c:
        c.execute(
            "INSERT INTO messages (session_id, role, content, ts) VALUES (?, ?, ?, ?)",
            (session_id, role, content, _now_ms()),
        )


def get_messages(session_id: str) -> list[dict[str, Any]]:
    with _conn() as c:
        rows = c.execute(
            "SELECT role, content, ts FROM messages WHERE session_id = ? ORDER BY ts ASC",
            (session_id,),
        ).fetchall()
    return [dict(r) for r in rows]


def save_playlist(session_id: str | None, name: str, prompt: str | None, tracks: list[dict]) -> int:
    with _conn() as c:
        cur = c.execute(
            "INSERT INTO playlists (session_id, name, prompt, tracks_json, created_at) VALUES (?, ?, ?, ?, ?)",
            (session_id, name, prompt, json.dumps(tracks), _now_ms()),
        )
        return int(cur.lastrowid or 0)


def list_playlists(session_id: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
    with _conn() as c:
        if session_id:
            rows = c.execute(
                "SELECT id, name, prompt, tracks_json, created_at FROM playlists WHERE session_id = ? ORDER BY created_at DESC LIMIT ?",
                (session_id, limit),
            ).fetchall()
        else:
            rows = c.execute(
                "SELECT id, name, prompt, tracks_json, created_at FROM playlists ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
    out = []
    for r in rows:
        d = dict(r)
        d["tracks"] = json.loads(d.pop("tracks_json"))
        out.append(d)
    return out
