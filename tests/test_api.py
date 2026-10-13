import pytest

# Import-only smoke tests. These exercise the FastAPI app wiring and rely on
# the heavy dependencies (crawl4ai, langchain, supabase). They are skipped
# automatically when those packages are not installed.
pytest.importorskip("fastapi")
pytest.importorskip("crawl4ai")
pytest.importorskip("langchain_google_genai")
pytest.importorskip("supabase")

from fastapi.testclient import TestClient
from main import app


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


def test_root_endpoint(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.json()["message"] == "Competitor Analysis API is up and running"


def test_routes_registered(client):
    paths = set(app.openapi()["paths"].keys())
    assert "/api/extract" in paths
    assert "/api/analyses" in paths
    assert "/api/analysis" in paths


def test_extract_rejects_invalid_user(client):
    # An unknown user_id is rejected before any scraping starts, so the
    # endpoint responds with 403 (or 500 if the DB lookup itself fails).
    with client.stream("GET", "/api/extract", params={"url": "https://example.com", "user_id": "unknown-user-xyz"}) as resp:
        assert resp.status_code in (403, 500)


def test_management_endpoints_validate_user(client):
    for path, params in [
        ("/api/analyses", {"user_id": "unknown-user-xyz"}),
        ("/api/analysis", {"url": "https://example.com", "user_id": "unknown-user-xyz"}),
    ]:
        resp = client.get(path, params=params)
        # Users are validated against the public_users table (403) or the
        # failure is surfaced as a 500 when the lookup itself errors.
        assert resp.status_code in (403, 500, 404)