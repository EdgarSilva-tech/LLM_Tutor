import sys
import types
import pytest
from fastapi.testclient import TestClient

from services.quizz_gen_service import main as main_mod
from services.quizz_gen_service.data_models import User


@pytest.fixture
def client(monkeypatch):
    app = main_mod.app

    async def _fake_user():
        return User(username="u", email="e", disabled=False)

    app.dependency_overrides[main_mod.get_current_active_user] = _fake_user
    return TestClient(app)


def test_health_disabled_when_no_rabbit_url(client, monkeypatch):
    monkeypatch.setattr(main_mod.quizz_settings, "RABBITMQ_URL", "")
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["rabbitmq"] == "disabled"


def test_health_ok_when_connects(client, monkeypatch):
    monkeypatch.setattr(main_mod.quizz_settings, "RABBITMQ_URL", "amqp://x")

    fake_module = types.ModuleType("aio_pika")

    class Conn:
        async def close(self):  # pragma: no cover - trivial
            return None

    async def connect_robust(url):  # pragma: no cover - simple stub
        return Conn()

    fake_module.connect_robust = connect_robust
    sys.modules["aio_pika"] = fake_module

    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["rabbitmq"] == "ok"


def test_health_error_on_exception(client, monkeypatch):
    monkeypatch.setattr(main_mod.quizz_settings, "RABBITMQ_URL", "amqp://x")

    fake_module = types.ModuleType("aio_pika")

    async def connect_robust(url):  # pragma: no cover - simple stub
        raise RuntimeError("boom")

    fake_module.connect_robust = connect_robust
    sys.modules["aio_pika"] = fake_module

    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["rabbitmq"] == "error"
