"""Regression test for the balanced-brace JSON extractor used by the agent's critique step."""
import json
from app.guardrails import extract_first_json


def test_extracts_simple_json():
    result = extract_first_json('{"a": 1, "b": 2}')
    assert json.loads(result) == {"a": 1, "b": 2}


def test_extracts_nested_json():
    """The critique schema uses nested objects in `issues`, which the prior regex broke."""
    raw = '{"issues": [{"index": 1, "reason": "wrong vibe"}, {"index": 3, "reason": "high energy"}], "reorder": [2, 5, 4]}'
    result = extract_first_json(raw)
    parsed = json.loads(result)
    assert len(parsed["issues"]) == 2
    assert parsed["reorder"] == [2, 5, 4]


def test_extracts_with_surrounding_text():
    raw = 'Sure! Here is the JSON:\n\n{"mode": "playlist", "duration_min": 45}\n\nLet me know if you need anything else.'
    result = extract_first_json(raw)
    assert json.loads(result) == {"mode": "playlist", "duration_min": 45}


def test_handles_strings_with_braces():
    """Don't get confused by braces inside string values."""
    raw = '{"title": "look at this {weird} text", "valid": true}'
    result = extract_first_json(raw)
    parsed = json.loads(result)
    assert parsed["title"] == "look at this {weird} text"


def test_returns_none_when_no_json():
    assert extract_first_json("hello world") is None
    assert extract_first_json("") is None
