from app.personas import PERSONAS, commentary


def test_four_personas_defined():
    assert set(PERSONAS.keys()) == {"warm", "snark", "nerd", "hype"}


def test_personas_produce_different_commentary():
    """Two personas with same input produce measurably different outputs."""
    picks = [
        {"title": "Sunrise City", "artist": "Neon Echo"},
        {"title": "Midnight Coding", "artist": "LoRoom"},
    ]
    query = "morning music"
    warm = commentary("warm", query, picks)
    snark = commentary("snark", query, picks)
    assert len(warm) > 10
    assert len(snark) > 10
    assert warm != snark
