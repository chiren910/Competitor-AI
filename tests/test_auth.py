import pytest
from fastapi.testclient import TestClient
from main import app
from utils.auth_service import (
    register_user, login_user, verify_session, delete_session
)


@pytest.fixture(scope="function")
def client():
    return TestClient(app)


def test_auth_registration_and_login():
    import uuid
    uid = uuid.uuid4().hex[:8]
    email = f"analyst_{uid}@domain.com"
    pwd = "securepassword123"
    name = "Test Analyst"

    # Register
    user, token = register_user(email, pwd, name, "Venture Alpha")
    assert user["email"] == email
    assert user["full_name"] == name
    assert token is not None

    # Verify session
    session_user = verify_session(token)
    assert session_user is not None
    assert session_user["email"] == email

    # Re-login
    login_u, new_tok = login_user(email, pwd)
    assert login_u["email"] == email
    assert new_tok is not None

    # Delete session (logout)
    delete_session(new_tok)
    assert verify_session(new_tok) is None


def test_auth_duplicate_email_rejected():
    import uuid
    uid = uuid.uuid4().hex[:8]
    email = f"duplicate_{uid}@domain.com"
    register_user(email, "pass12345", "Original User")
    with pytest.raises(ValueError, match="already exists"):
        register_user(email, "pass12345", "Duplicate User")


def test_auth_invalid_password_rejected():
    with pytest.raises(ValueError, match="at least 6 characters"):
        register_user("short_pwd@domain.com", "123", "Short User")


def test_unauthenticated_dashboard_redirects_to_login(client):
    # Unauthenticated GET /dashboard must strictly redirect to /login
    resp = client.get("/dashboard", follow_redirects=False)
    assert resp.status_code == 303
    assert resp.headers["location"] == "/login"


def test_authenticated_dashboard_access(client):
    # Register/login via API
    resp = client.post("/api/auth/login", json={
        "email": "demo@competitor.ai",
        "password": "password123"
    })
    assert resp.status_code == 200
    token = resp.json()["token"]

    # Now access /dashboard with cookie
    client.cookies.set("ca_session_token", token)
    dash_resp = client.get("/dashboard", follow_redirects=False)
    assert dash_resp.status_code == 200


def test_browser_root_redirects_to_login_if_unauthenticated(client):
    # Browser client asking for HTML without auth is redirected to /login
    resp = client.get("/", headers={"accept": "text/html,application/xhtml+xml"}, follow_redirects=False)
    assert resp.status_code == 303
    assert resp.headers["location"] == "/login"
