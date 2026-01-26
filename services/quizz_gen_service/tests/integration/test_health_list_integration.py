import json
import pytest
import redis
from fastapi.testclient import TestClient

from services.quizz_gen_service import main as q_main
from services.quizz_gen_service.quizz_settings import quizz_settings
from services.quizz_gen_service.data_models import User

pytestmark = pytest.mark.integration


@pytest.fixture(autouse=True)
def _redis_client(monkeypatch):
    r = redis.Redis(
        host=quizz_settings.REDIS_ENDPOINT,
        port=quizz_settings.REDIS_PORT,
        username=quizz_settings.REDIS_USERNAME,
        password=quizz_settings.REDIS_PASSWORD,
        decode_responses=True,
        socket_connect_timeout=2,
        socket_timeout=2,
        health_check_interval=10,
    )
    # clean any test keys
    for k in list(r.scan_iter("quizz_request:u:*")):
        r.delete(k)
    monkeypatch.setattr(q_main, "redis_client", r, raising=True)
    yield
    for k in list(r.scan_iter("quizz_request:u:*")):
        r.delete(k)


@pytest.fixture()
def client(monkeypatch):
    async def _fake_user():
        return User(username="u", email="u@example.com", disabled=False)

    app = q_main.app
    app.dependency_overrides[q_main.get_current_active_user] = _fake_user
    return TestClient(app)


def test_health_disabled_rabbitmq(client, monkeypatch):
    # Force disable rabbit by clearing URL on the imported settings instance
    monkeypatch.setattr(q_main.quizz_settings, "RABBITMQ_URL", "", raising=True)
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["service"] == "Quiz Generation Service"
    assert data["rabbitmq"] == "disabled"


def test_get_quizz_questions_lists_values(client):
    # Seed some quizz_request keys for user 'u'
    r: redis.Redis = q_main.redis_client
    r.set("quizz_request:u:1", json.dumps(["Q1", "Q2"]))
    r.set("quizz_request:u:2", json.dumps(["Q3"]))

    res = client.get("/get-quizz-questions", headers={"Authorization": "Bearer dummy"})
    assert res.status_code == 200
    values = res.json()
    assert isinstance(values, list)
    decoded = [json.loads(v) for v in values if v]
    assert ["Q1", "Q2"] in decoded
    assert ["Q3"] in decoded


def test_health_error_when_broker_unreachable(client, monkeypatch):
    # Ensure URL is "set" so health tries to connect
    monkeypatch.setattr(
        q_main.quizz_settings,
        "RABBITMQ_URL",
        "amqp://user:pass@localhost/%2F",
        raising=True,
    )

    # Provide a dummy aio_pika with a failing connect_robust
    import types
    import sys
    import asyncio as _asyncio

    async def _fail_connect(url):
        await _asyncio.sleep(0)
        raise RuntimeError("cannot reach broker")

    dummy = types.SimpleNamespace(connect_robust=_fail_connect)
    monkeypatch.setitem(sys.modules, "aio_pika", dummy)

    res = client.get("/health")
    assert res.status_code == 200
    body = res.json()
    assert body["service"] == "Quiz Generation Service"
    assert body["rabbitmq"] == "error"
