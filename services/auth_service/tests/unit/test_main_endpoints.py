import pytest
from fastapi.testclient import TestClient

from services.auth_service import main as main_mod
from services.auth_service.data_models import User


@pytest.fixture
def client():
    return TestClient(main_mod.app)


def test_token_success(client, monkeypatch):
    class FakeUser:
        def __init__(self):
            self.username = "u"

    def fake_auth(username, password):
        return FakeUser()

    def fake_create_token(data, expires_delta=None):
        return "tok"

    monkeypatch.setattr(main_mod, "authenticate_user", fake_auth)
    monkeypatch.setattr(main_mod, "create_access_token", fake_create_token)

    resp = client.post(
        "/token",
        data={"username": "u", "password": "p"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["access_token"] == "tok"
    assert body["token_type"] == "bearer"


def test_token_wrong_password_401(client, monkeypatch):
    def fake_auth(username, password):
        return False

    monkeypatch.setattr(main_mod, "authenticate_user", fake_auth)

    resp = client.post(
        "/token",
        data={"username": "u", "password": "bad"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert resp.status_code == 401
    assert resp.headers.get("www-authenticate") == "Bearer"


def test_users_me_returns_user(client, monkeypatch):
    async def fake_get_current_active_user():
        return User(username="u", email="e", full_name="U", disabled=False)

    main_mod.app.dependency_overrides[main_mod.get_current_active_user] = (
        fake_get_current_active_user
    )

    resp = client.get("/users/me/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["username"] == "u"
    assert data["email"] == "e"
    assert data["full_name"] == "U"
    assert data["disabled"] is False

    main_mod.app.dependency_overrides.clear()


def test_users_me_items_returns_items(client, monkeypatch):
    async def fake_get_current_active_user():
        return User(username="u", email="e", full_name="U", disabled=False)

    main_mod.app.dependency_overrides[main_mod.get_current_active_user] = (
        fake_get_current_active_user
    )

    resp = client.get("/users/me/items/")
    assert resp.status_code == 200
    items = resp.json()
    assert isinstance(items, list)
    assert items[0]["owner"] == "u"

    main_mod.app.dependency_overrides.clear()


def test_signup_success(client, monkeypatch):
    def fake_get_user(username):
        return None

    class NewUser:
        def __init__(self):
            self.username = "u"
            self.email = "e"
            self.full_name = "U"
            self.disabled = False

    def fake_add_user(username, email, full_name, password):
        return NewUser()

    monkeypatch.setattr(main_mod, "get_user", fake_get_user)
    monkeypatch.setattr(main_mod, "add_user", fake_add_user)

    body = {"username": "u", "email": "e", "full_name": "U", "password": "p"}
    resp = client.post("/signup", json=body)
    assert resp.status_code == 200
    data = resp.json()
    assert data["username"] == "u"
    assert "hashed_password" not in data


def test_signup_duplicate_400(client, monkeypatch):
    class ExistingUser:
        def __init__(self):
            self.username = "u"

    def fake_get_user(username):
        return ExistingUser()

    monkeypatch.setattr(main_mod, "get_user", fake_get_user)

    body = {"username": "u", "email": "e", "full_name": "U", "password": "p"}
    resp = client.post("/signup", json=body)
    assert resp.status_code == 400


def test_signup_add_user_error_500(client, monkeypatch):
    def fake_get_user(username):
        return None

    def fake_add_user(*a, **k):
        raise RuntimeError("db error")

    monkeypatch.setattr(main_mod, "get_user", fake_get_user)
    monkeypatch.setattr(main_mod, "add_user", fake_add_user)

    body = {"username": "u", "email": "e", "full_name": "U", "password": "p"}
    resp = client.post("/signup", json=body)
    assert resp.status_code == 500
