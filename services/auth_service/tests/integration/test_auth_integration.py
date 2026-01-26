import uuid
import pytest
from fastapi.testclient import TestClient
from sqlmodel import create_engine

from services.auth_service import main as auth_main
from services.auth_service import user_db
from services.auth_service import auth_utils


pytestmark = pytest.mark.integration


@pytest.fixture()
def client(tmp_path, monkeypatch):
    # Use a temporary SQLite database for integration tests
    db_file = tmp_path / f"auth_{uuid.uuid4().hex}.db"
    engine = create_engine(
        f"sqlite:///{db_file}?check_same_thread=False",
        echo=False,
    )

    # Patch engines in both modules to point to SQLite instead of Postgres
    monkeypatch.setattr(user_db, "engine", engine, raising=True)
    monkeypatch.setattr(auth_utils, "engine", engine, raising=True)

    # Ensure JWT secret is present (auth_utils reads AUTH_SECRET at import; patch it directly)
    monkeypatch.setattr(auth_utils, "AUTH_SECRET", "test-secret", raising=True)

    # Construct app after patches so lifespan will create tables on our engine
    app = auth_main.app
    with TestClient(app) as test_client:
        yield test_client


def test_signup_and_token_and_me_flow(client: TestClient):
    # 1) Signup a new user
    payload = {
        "username": "alice",
        "email": "alice@example.com",
        "full_name": "Alice Doe",
        "password": "s3cret!",
    }
    r = client.post("/signup", json=payload)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["username"] == "alice"
    assert body["email"] == "alice@example.com"
    assert body["disabled"] is False

    # 2) Obtain token
    token_res = client.post(
        "/token",
        data={"username": "alice", "password": "s3cret!"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert token_res.status_code == 200, token_res.text
    tok = token_res.json()["access_token"]
    assert tok

    # 3) Call /users/me with Bearer token
    me = client.get("/users/me/", headers={"Authorization": f"Bearer {tok}"})
    assert me.status_code == 200, me.text
    data = me.json()
    assert data["username"] == "alice"
    assert data["email"] == "alice@example.com"

    # 4) Wrong password → 401
    bad = client.post(
        "/token",
        data={"username": "alice", "password": "wrong"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert bad.status_code == 401


def test_duplicate_signup_returns_400(client: TestClient):
    # First signup should succeed
    payload = {
        "username": "bob",
        "email": "bob@example.com",
        "full_name": "Bob",
        "password": "pw",
    }
    r1 = client.post("/signup", json=payload)
    assert r1.status_code == 200, r1.text

    # Second signup with same username should fail with 400
    r2 = client.post("/signup", json=payload)
    assert r2.status_code == 400
    body = r2.json()
    assert "Username already registered" in body.get("detail", "")
