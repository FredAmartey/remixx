from app.intent import classify_intent


def test_chat_intent_for_short_request():
    result = classify_intent("play me something for late at night")
    assert result["mode"] in {"chat", "playlist", "taste"}


def test_playlist_intent_when_duration_named():
    result = classify_intent("build me a 45 minute focus playlist")
    assert result["mode"] == "playlist"
    assert result["duration_min"] == 45


def test_taste_intent_when_song_list_pasted():
    result = classify_intent(
        "here are 5 songs i love: Massive Attack — Teardrop, "
        "Mount Kimbie — Made to Stray, Bonobo — Cirrus, "
        "Tycho — Awake, Boards of Canada — Roygbiv"
    )
    assert result["mode"] == "taste"
    assert len(result["seed_songs"]) >= 3
