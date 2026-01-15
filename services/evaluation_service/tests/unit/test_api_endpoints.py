import json
import pytest
from fastapi.testclient import TestClient

from services.evaluation_service import main as main_mod
from services.evaluation_service.data_models import User


class FakeRedis:
    def __init__(self):
        self.store = {}

    def get(self, key):
        return self.store.get(key)

    def set(self, key, value):
        self.store[key] = value

    def scan(self, cursor=0, match=None, count=10):
        # retorna cursor=0 para parar o loop e todas as chaves que combinam
        keys = [
            k
            for k in self.store.keys()
            if (match is None or k.startswith(match.split("*")[0]))
        ]
        return 0, keys[:count]

    def mget(self, keys):
        return [self.store.get(k) for k in keys]


@pytest.fixture(autouse=True)
def client_with_user(monkeypatch):
    async def _fake_user():
        return User(username="u", email="e", full_name="U", disabled=False)

    main_mod.app.dependency_overrides[main_mod.get_current_active_user] = _fake_user
    return TestClient(main_mod.app)


def test_health_rabbit_disabled(client_with_user, monkeypatch):
    from services.evaluation_service.eval_settings import eval_settings

    monkeypatch.setattr(eval_settings, "RABBITMQ_URL", "")
    resp = client_with_user.get("/health")
    assert resp.status_code == 200
    assert resp.json()["rabbitmq"] == "disabled"


@pytest.mark.asyncio
async def test_health_rabbit_ok(client_with_user, monkeypatch):
    from services.evaluation_service.eval_settings import eval_settings

    monkeypatch.setattr(
        eval_settings, "RABBITMQ_URL", "amqp://guest:guest@localhost:5672/"
    )

    class Conn:
        async def close(self):
            pass

    async def _ok(*a, **k):
        return Conn()

    monkeypatch.setattr("aio_pika.connect_robust", _ok)
    r = client_with_user.get("/health")
    assert r.status_code == 200
    assert r.json()["rabbitmq"] == "ok"


@pytest.mark.asyncio
async def test_health_rabbit_error(client_with_user, monkeypatch):
    from services.evaluation_service.eval_settings import eval_settings

    monkeypatch.setattr(
        eval_settings, "RABBITMQ_URL", "amqp://guest:guest@localhost:5672/"
    )

    async def _err(*a, **k):
        raise RuntimeError("conn fail")

    monkeypatch.setattr("aio_pika.connect_robust", _err)
    r = client_with_user.get("/health")
    assert r.status_code == 200
    assert r.json()["rabbitmq"] == "error"


def test_eval_service_success(client_with_user, monkeypatch):
    # Fake Redis + persistência
    r = FakeRedis()
    monkeypatch.setattr(main_mod, "redis_client", r)

    calls = {"saved": []}

    def fake_store(username, q, a, correct, score, feedback):
        calls["saved"].append((username, q, a, correct, score, feedback))

    monkeypatch.setattr(main_mod, "store_evals", fake_store)

    class AIMessage:
        def __init__(self, content):
            self.content = content

    def fake_eval_answer(question, answer):
        return AIMessage(
            json.dumps({"correct_answer": "X", "score": 0.9, "feedback": "ok"})
        )

    monkeypatch.setattr(main_mod, "eval_answer", fake_eval_answer)

    body = {
        "student_id": "u",
        "quizz_questions": ["Q1", "Q2"],
        "student_answers": ["a1", "a2"],
    }
    resp = client_with_user.post(
        "/eval-service", json=body, headers={"Authorization": "Bearer t"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "request_id" in data and "feedback" in data
    assert len(calls["saved"]) == 2
    # verifica cache
    assert any(k.startswith("Eval:u:") for k in r.store.keys())


def test_eval_service_error_500(client_with_user, monkeypatch):
    r = FakeRedis()
    monkeypatch.setattr(main_mod, "redis_client", r)

    def boom(*a, **k):
        raise RuntimeError("llm fail")

    monkeypatch.setattr(main_mod, "eval_answer", boom)

    body = {
        "student_id": "u",
        "quizz_questions": ["Q1"],
        "student_answers": ["a1"],
    }
    resp = client_with_user.post(
        "/eval-service", json=body, headers={"Authorization": "Bearer t"}
    )
    assert resp.status_code == 500


def test_evaluate_answer_success(client_with_user, monkeypatch):
    class AIMessage:
        def __init__(self, content):
            self.content = content

    monkeypatch.setattr(main_mod, "eval_answer", lambda q, a: AIMessage('{"score": 1}'))
    resp = client_with_user.post(
        "/eval-service/evaluate_answer", json={"question": "Q", "answer": "A"}
    )
    assert resp.status_code == 200
    assert resp.json()["score"] == 1


def test_evaluate_answer_error(client_with_user, monkeypatch):
    monkeypatch.setattr(
        main_mod, "eval_answer", lambda q, a: (_ for _ in ()).throw(RuntimeError("x"))
    )
    resp = client_with_user.post(
        "/eval-service/evaluate_answer", json={"question": "Q", "answer": "A"}
    )
    assert resp.status_code == 500


def test_get_feedback_with_results(client_with_user, monkeypatch):
    r = FakeRedis()
    # Simula duas entradas
    r.set("Eval:u:1", json.dumps({"score": 0.5}))
    r.set("Eval:u:2", json.dumps({"score": 0.8}))
    monkeypatch.setattr(main_mod, "redis_client", r)

    resp = client_with_user.get(
        "/eval-service/get-feedback", headers={"Authorization": "Bearer t"}
    )
    assert resp.status_code == 200
    values = resp.json()
    assert isinstance(values, list)
    assert any('"score": 0.5' in v for v in values if v)


def test_get_feedback_no_keys(client_with_user, monkeypatch):
    r = FakeRedis()
    monkeypatch.setattr(main_mod, "redis_client", r)
    resp = client_with_user.get(
        "/eval-service/get-feedback", headers={"Authorization": "Bearer t"}
    )
    assert resp.status_code == 200
    assert resp.json() == "No keys found for the pattern."


def test_jobs_processing_and_done(client_with_user, monkeypatch):
    r = FakeRedis()
    monkeypatch.setattr(main_mod, "redis_client", r)

    # processing
    resp = client_with_user.get(
        "/eval-service/jobs/jobX", headers={"Authorization": "Bearer t"}
    )
    assert resp.status_code == 200
    assert resp.json() == {"status": "processing"}

    # done (json)
    r.set("Eval:u:jobX", json.dumps([{"score": 1}]))
    resp2 = client_with_user.get(
        "/eval-service/jobs/jobX", headers={"Authorization": "Bearer t"}
    )
    assert resp2.status_code == 200
    assert resp2.json()["status"] == "done"
