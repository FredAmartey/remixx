"""Lightweight API smoke tests. We avoid hitting LLM endpoints here — those are
exercised manually in Phase 3.3. These just verify the app imports, models validate,
and the no-LLM endpoints (healthz, personas, catalog) work."""
from fastapi.testclient import TestClient

from app.main import app


def test_app_imports_and_starts():
    client = TestClient(app)
    r = client.get("/healthz")
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert body["catalog_size"] == 500
    assert set(body["personas"]) == {"warm", "snark", "nerd", "hype"}


def test_personas_endpoint():
    client = TestClient(app)
    r = client.get("/personas")
    assert r.status_code == 200
    personas = r.json()
    assert len(personas) == 4
    keys = {p["key"] for p in personas}
    assert keys == {"warm", "snark", "nerd", "hype"}


def test_catalog_404_for_unknown_track():
    client = TestClient(app)
    r = client.get("/catalog/does-not-exist")
    assert r.status_code == 404
