"""SQLite persistence smoke tests."""
import pytest

from app import db


@pytest.fixture(autouse=True)
def _ensure_schema():
    db.init_db()


def test_create_session_returns_uuid():
    sid = db.create_session()
    assert len(sid) >= 16
    assert all(c in "0123456789abcdef" for c in sid)


def test_add_and_get_messages():
    sid = db.create_session()
    db.add_message(sid, "user", "hello")
    db.add_message(sid, "assistant", "hi")
    msgs = db.get_messages(sid)
    assert len(msgs) == 2
    assert msgs[0]["role"] == "user"
    assert msgs[1]["content"] == "hi"


def test_save_and_list_playlists():
    sid = db.create_session()
    pid = db.save_playlist(sid, "Test Mix", "vibe prompt", [{"id": "x", "title": "Song"}])
    assert pid > 0
    rows = db.list_playlists(session_id=sid)
    assert len(rows) >= 1
    assert rows[0]["name"] == "Test Mix"
    assert rows[0]["tracks"][0]["title"] == "Song"
