import json
import pytest
from fastapi.testclient import TestClient

from services.quizz_gen_service import main as main_mod
from services.quizz_gen_service.data_models import User
from fnmatch import fnmatch


class FakeRedis:
    def __init__(self):
        self.store = {}

    def get(self, key):
        return self.store.get(key)

    def setex(self, key, ttl, value):
        self.store[key] = value

    def scan(self, cursor=0, match=None, count=10):
        keys = [k for k in self.store.keys() if match is None or fnmatch(k, match)]
        return 0, keys[:count]

    def mget(self, keys):
        return [self.store.get(k) for k in keys]


@pytest.fixture(autouse=True)
def client_with_user(monkeypatch):
    app = main_mod.app

    async def _fake_user():
        return User(username="u", email="e", disabled=False)

    app.dependency_overrides[main_mod.get_current_active_user] = _fake_user
    return TestClient(app)


@pytest.fixture
def fake_redis(monkeypatch):
    r = FakeRedis()
    monkeypatch.setattr(main_mod, "redis_client", r)
    return r


def test_jobs_returns_processing_when_missing(client_with_user, fake_redis):
    resp = client_with_user.get("/jobs/any-id", headers={"Authorization": "Bearer t"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "processing"


def test_jobs_parses_json(client_with_user, fake_redis):
    key = "Quiz:u:job-1"
    fake_redis.setex(key, 10, json.dumps({"status": "queued"}))
    resp = client_with_user.get("/jobs/job-1", headers={"Authorization": "Bearer t"})
    assert resp.status_code == 200
    assert resp.json() == {"status": "queued"}


def test_jobs_returns_done_with_raw_value(client_with_user, fake_redis):
    key = "Quiz:u:job-2"
    fake_redis.setex(key, 10, "['Q1','Q2']")  # valor não-JSON-objeto -> cai no except
    resp = client_with_user.get("/jobs/job-2", headers={"Authorization": "Bearer t"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "done"
    assert data["questions"] == "['Q1','Q2']"


def test_submit_answers_404_when_quiz_missing(client_with_user, fake_redis):
    body = {"quiz_id": "missing", "answers": ["a"]}
    resp = client_with_user.post(
        "/submit-answers", json=body, headers={"Authorization": "Bearer t"}
    )
    assert resp.status_code == 404


def test_submit_answers_400_on_count_mismatch(client_with_user, fake_redis):
    key = "Quiz:u:q1"
    fake_redis.setex(key, 10, json.dumps(["Q1", "Q2"]))
    body = {"quiz_id": "q1", "answers": ["a"]}  # 1 resposta para 2 questões
    resp = client_with_user.post(
        "/submit-answers", json=body, headers={"Authorization": "Bearer t"}
    )
    assert resp.status_code == 400


def test_submit_answers_success_publishes(client_with_user, fake_redis, monkeypatch):
    key = "Quiz:u:q2"
    fake_redis.setex(key, 10, json.dumps(["Q1", "Q2"]))

    captured = {}

    async def fake_publish(payload, rk):
        captured["payload"] = payload

    # Patch new async publisher used by background task
    monkeypatch.setattr(
        "services.quizz_gen_service.mq._publish_with_retry", fake_publish, raising=True
    )

    body = {"quiz_id": "q2", "answers": ["a1", "a2"]}
    resp = client_with_user.post(
        "/submit-answers", json=body, headers={"Authorization": "Bearer t"}
    )
    assert resp.status_code == 202
    job = resp.json()
    assert "job_id" in job
    assert "payload" in captured
    assert captured["payload"]["quizz_questions"] == ["Q1", "Q2"]
    assert captured["payload"]["student_answers"] == ["a1", "a2"]


def test_get_quizz_questions_returns_values(client_with_user, fake_redis, monkeypatch):
    # simula duas entradas cacheadas
    fake_redis.setex("quizz_request:u:hash1", 10, json.dumps(["Q1"]))
    fake_redis.setex("quizz_request:u:hash2", 10, json.dumps(["Q2"]))

    resp = client_with_user.get(
        "/get-quizz-questions", headers={"Authorization": "Bearer t"}
    )
    assert resp.status_code == 200
    values = resp.json()
    # retorna array de strings (JSON) conforme implementação atual
    assert isinstance(values, list)
    assert any('"Q1"' in v for v in values if v)
    assert any('"Q2"' in v for v in values if v)
