import pytest
from fastapi.testclient import TestClient

from services.quizz_gen_service import main as main_mod
from services.quizz_gen_service.data_models import User


class FakeRedisEmpty:
    def scan(self, cursor=0, match=None, count=10):
        return 0, []

    def mget(self, keys):
        return []


@pytest.fixture(autouse=True)
def client_with_user(monkeypatch):
    app = main_mod.app

    async def _fake_user():
        return User(username="u", email="e", disabled=False)

    app.dependency_overrides[main_mod.get_current_active_user] = _fake_user
    return TestClient(app)


def test_get_quizz_questions_empty_returns_message(client_with_user, monkeypatch):
    monkeypatch.setattr(main_mod, "redis_client", FakeRedisEmpty())
    resp = client_with_user.get(
        "/get-quizz-questions", headers={"Authorization": "Bearer t"}
    )
    assert resp.status_code == 200
    assert resp.json() == "No keys found for the pattern."
