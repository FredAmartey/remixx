from app.reranker import score_song, rerank


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
