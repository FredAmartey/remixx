from app.reranker import infer_query_overrides, score_song, rerank


def test_genre_match_scores_two_points():
    user = {"genre": "rock", "mood": "intense", "energy": 0.8, "likes_acoustic": False}
    song = {"genre": "rock", "mood": "intense", "energy": 0.85, "valence": 0.5,
            "danceability": 0.7, "acousticness": 0.1}
    score, reasons = score_song(user, song)
    assert any("genre match" in r for r in reasons)
    assert score >= 2.0


def test_returns_tuple_of_score_and_reasons():
    user = {"genre": "pop", "mood": "happy", "energy": 0.5, "likes_acoustic": False}
    song = {"genre": "lofi", "mood": "chill", "energy": 0.5, "valence": 0.5,
            "danceability": 0.5, "acousticness": 0.5}
    score, reasons = score_song(user, song)
    assert isinstance(score, float)
    assert isinstance(reasons, list)


def test_rerank_returns_top_k_sorted_with_attached_score():
    user = {"genre": "rock", "mood": "intense", "energy": 0.8, "likes_acoustic": False}
    candidates = [
        {"id": "a", "genre": "rock", "mood": "intense", "energy": 0.9, "valence": 0.5, "danceability": 0.6, "acousticness": 0.1},
        {"id": "b", "genre": "pop", "mood": "happy", "energy": 0.4, "valence": 0.7, "danceability": 0.5, "acousticness": 0.3},
        {"id": "c", "genre": "rock", "mood": "moody", "energy": 0.7, "valence": 0.4, "danceability": 0.4, "acousticness": 0.2},
    ]
    result = rerank(user, candidates, k=2)
    assert len(result) == 2
    assert result[0]["_score"] >= result[1]["_score"]
    assert "_reasons" in result[0]


def test_rerank_uses_retrieval_relevance_as_tiebreaker():
    user = {"genre": "study", "mood": "chill", "energy": 0.35, "likes_acoustic": False}
    candidates = [
        {
            "id": "weak",
            "genre": "study",
            "mood": "chill",
            "energy": 0.35,
            "valence": 0.35,
            "danceability": 0.5,
            "acousticness": 0.1,
            "_rag_score": 0.01,
        },
        {
            "id": "strong",
            "genre": "study",
            "mood": "chill",
            "energy": 0.35,
            "valence": 0.35,
            "danceability": 0.5,
            "acousticness": 0.1,
            "_rag_score": 0.2,
        },
    ]
    result = rerank(user, candidates, k=2)
    assert result[0]["id"] == "strong"
    assert any("retrieval match" in r for r in result[0]["_reasons"])


def test_slow_night_query_adds_energy_guardrail():
    prefs = infer_query_overrides("slow hopeful late-night songs with room to breathe")
    assert prefs["energy"] <= 0.42
    assert prefs["max_energy"] <= 0.65
    assert "hardstyle" in prefs["excluded_genres"]


def test_deep_focus_no_sharp_edges_is_low_energy():
    prefs = infer_query_overrides("deep focus music with no sharp edges and steady momentum")
    assert prefs["mood"] == "chill"
    assert prefs["energy"] <= 0.34
    assert prefs["max_energy"] <= 0.55


def test_energy_guardrail_penalizes_obvious_mismatch():
    user = {
        "genre": "pop",
        "mood": "relaxed",
        "energy": 0.35,
        "max_energy": 0.55,
        "likes_acoustic": False,
        "excluded_genres": {"hardstyle"},
    }
    quiet = {
        "genre": "pop",
        "mood": "relaxed",
        "energy": 0.4,
        "valence": 0.4,
        "danceability": 0.4,
        "acousticness": 0.2,
    }
    hardstyle = {
        "genre": "hardstyle",
        "mood": "intense",
        "energy": 0.9,
        "valence": 0.4,
        "danceability": 0.7,
        "acousticness": 0.1,
    }
    quiet_score, _ = score_song(user, quiet)
    hardstyle_score, reasons = score_song(user, hardstyle)
    assert quiet_score > hardstyle_score
    assert any("genre guardrail" in r for r in reasons)
