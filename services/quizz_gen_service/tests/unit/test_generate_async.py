import json
import pytest
from fastapi.testclient import TestClient

from services.quizz_gen_service import main as main_mod
from services.quizz_gen_service.data_models import User


class FakeRedis:
    def __init__(self):
        self.store = {}

    def setex(self, key, ttl, value):
        self.store[key] = value


@pytest.fixture(autouse=True)
def fake_redis(monkeypatch):
    r = FakeRedis()
    monkeypatch.setattr(main_mod, "redis_client", r)
    return r


@pytest.fixture(autouse=True)
def mock_publish(monkeypatch):
    # Evita abrir conexão com RabbitMQ no background task
    async def _noop(*args, **kwargs):
        return None

    monkeypatch.setattr("services.quizz_gen_service.mq._publish_with_retry", _noop)


@pytest.fixture
def client():
    app = main_mod.app

    async def _fake_user():
        return User(username="u", email="e", disabled=False)

    app.dependency_overrides[main_mod.get_current_active_user] = _fake_user
    return TestClient(app)


def test_generate_async_queues_and_returns_202(client, fake_redis):
    body = {
        "topic": "linear algebra",
        "num_questions": 3,
        "difficulty": "easy",
        "style": "conceptual",
    }
    resp = client.post(
        "/generate-async",
        json=body,
        headers={"Authorization": "Bearer token"},
    )
    assert resp.status_code == 202
    data = resp.json()
    assert "quiz_id" in data
    assert data["status"] == "queued"

    key = f"Quiz:u:{data['quiz_id']}"
    assert key in fake_redis.store
    payload = json.loads(fake_redis.store[key])
    assert payload["status"] == "queued"
