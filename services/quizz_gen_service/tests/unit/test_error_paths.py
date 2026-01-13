import json
import pytest
from fastapi.testclient import TestClient

from services.quizz_gen_service import main as main_mod
from services.quizz_gen_service.data_models import User


class FailingRedis:
    def __init__(self):
        self.store = {}

    def get(self, key):
        raise RuntimeError("redis down")

    def setex(self, key, ttl, value):
        self.store[key] = value

    def scan(self, *a, **k):
        raise RuntimeError("redis down")

    def mget(self, *a, **k):
        raise RuntimeError("redis down")


@pytest.fixture
def client(monkeypatch):
    app = main_mod.app

    async def _fake_user():
        return User(username="u", email="e", disabled=False)

    app.dependency_overrides[main_mod.get_current_active_user] = _fake_user
    return TestClient(app)


def test_generate_quiz_error_returns_500(client, monkeypatch):
    def boom(*a, **k):
        raise RuntimeError("boom")

    monkeypatch.setattr(main_mod, "quizz_generator", boom)

    body = {
        "topic": "t",
        "num_questions": 2,
        "difficulty": "easy",
        "style": "conceptual",
    }
    resp = client.post(
        "/generate-quiz", json=body, headers={"Authorization": "Bearer t"}
    )
    assert resp.status_code == 500


def test_create_quiz_error_returns_500(client, monkeypatch):
    def boom(*a, **k):
        raise RuntimeError("boom")

    monkeypatch.setattr(main_mod, "quizz_generator", boom)

    body = {
        "topic": "t",
        "num_questions": 2,
        "difficulty": "easy",
        "style": "conceptual",
    }
    resp = client.post("/create-quiz", json=body, headers={"Authorization": "Bearer t"})
    assert resp.status_code == 500


def test_submit_answers_publisher_failure_returns_500(client, monkeypatch):
    # Redis tem o quiz e as perguntas; publisher falha
    class RedisOK:
        def __init__(self):
            self.store = {}

        def get(self, key):
            return json.dumps(["Q1", "Q2"])

        def setex(self, k, ttl, v):
            self.store[k] = v

    monkeypatch.setattr(main_mod, "redis_client", RedisOK())

    def publisher_boom(payload):
        raise RuntimeError("publish failed")

    monkeypatch.setattr(main_mod, "publish_evaluation_request_sync", publisher_boom)

    body = {"quiz_id": "q1", "answers": ["a1", "a2"]}
    resp = client.post(
        "/submit-answers", json=body, headers={"Authorization": "Bearer t"}
    )
    assert resp.status_code == 500


def test_jobs_returns_processing_on_redis_error(client, monkeypatch):
    monkeypatch.setattr(main_mod, "redis_client", FailingRedis())
    resp = client.get("/jobs/any", headers={"Authorization": "Bearer t"})
    assert resp.status_code == 200
    assert resp.json() == {"status": "processing"}


def test_generate_async_marks_failed_when_publish_fails(client, monkeypatch):
    # Redis de teste que grava setex para verificarmos a marcação de failed
    class RedisProbe:
        def __init__(self):
            self.store = {}

        def setex(self, key, ttl, value):
            self.store[key] = value

        def get(self, key):
            return self.store.get(key)

    r = RedisProbe()
    monkeypatch.setattr(main_mod, "redis_client", r)

    async def publish_fail(*a, **k):
        raise RuntimeError("broker down")

    # Força o publish em background a falhar
    monkeypatch.setattr(
        "services.quizz_gen_service.mq._publish_with_retry", publish_fail
    )

    body = {
        "topic": "t",
        "num_questions": 1,
        "difficulty": "easy",
        "style": "conceptual",
    }
    resp = client.post(
        "/generate-async", json=body, headers={"Authorization": "Bearer t"}
    )
    assert resp.status_code == 202

    # Como a task roda no ciclo da requisição do TestClient, a marcação deve existir
    # Descobre a chave pelo único item do store
    assert len(r.store) >= 1
    # pega o último valor gravado (status "failed" deve ter sobrescrito o "queued")
    last_value = list(r.store.values())[-1]
    assert json.loads(last_value)["status"] == "failed"
