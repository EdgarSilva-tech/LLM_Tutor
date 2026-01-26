import json
import asyncio
import time
import pytest
import redis
from fastapi.testclient import TestClient

from services.quizz_gen_service import main as main_mod
from services.quizz_gen_service.data_models import User
from services.quizz_gen_service.quizz_settings import quizz_settings


pytestmark = pytest.mark.integration


@pytest.fixture(autouse=True)
def _redis_setup(monkeypatch):
    # Use configured endpoint/port (CI should provide reachable Redis)
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
    # Clean user namespace
    for k in list(r.scan_iter("Quiz:u:*")):
        r.delete(k)
    monkeypatch.setattr(main_mod, "redis_client", r)
    yield
    for k in list(r.scan_iter("Quiz:u:*")):
        r.delete(k)


@pytest.fixture()
def client(monkeypatch):
    async def _fake_user():
        return User(username="u", email="u@example.com", disabled=False)

    app = main_mod.app
    app.dependency_overrides[main_mod.get_current_active_user] = _fake_user
    return TestClient(app)


def test_generate_async_sets_queued_and_jobs_progress(client, monkeypatch):
    # Stub async publisher to no-op so we don't require RabbitMQ
    async def _noop_publish(payload):
        await asyncio.sleep(0)
        return None

    from services.quizz_gen_service import mq as mq_mod

    monkeypatch.setattr(mq_mod, "_publish_with_retry", _noop_publish)

    body = {
        "topic": "vectors",
        "num_questions": 2,
        "difficulty": "easy",
        "style": "conceptual",
    }
    res = client.post(
        "/generate-async", json=body, headers={"Authorization": "Bearer t"}
    )
    assert res.status_code == 202
    quiz_id = res.json().get("quiz_id")
    assert quiz_id

    # Immediately after, job status should be queued/processing (not done)
    jr = client.get(f"/jobs/{quiz_id}", headers={"Authorization": "Bearer t"})
    assert jr.status_code == 200
    stat = jr.json().get("status")
    assert stat in ("queued", "processing")

    # Simulate consumer writing result into Redis
    r: redis.Redis = main_mod.redis_client
    key = f"Quiz:u:{quiz_id}"
    r.setex(
        key,
        3600,
        json.dumps({"status": "done", "questions": ["Q1", "Q2"]}),
    )

    jr2 = client.get(f"/jobs/{quiz_id}", headers={"Authorization": "Bearer t"})
    assert jr2.status_code == 200
    data = jr2.json()
    assert data.get("status") == "done"
    assert data.get("questions") == ["Q1", "Q2"]


def test_submit_answers_mismatch_returns_400(client):
    # Seed a quiz with 2 questions
    r: redis.Redis = main_mod.redis_client
    quiz_id = "qid-123"
    key = f"Quiz:u:{quiz_id}"
    r.setex(key, 3600, json.dumps({"status": "done", "questions": ["Q1", "Q2"]}))

    # Provide only one answer → should 400
    resp = client.post(
        "/submit-answers",
        json={"quiz_id": quiz_id, "answers": ["only-one"]},
        headers={"Authorization": "Bearer t"},
    )
    assert resp.status_code == 400


def test_jobs_failure_status_is_returned(client):
    # Simulate consumer marking job as failed in Redis
    r: redis.Redis = main_mod.redis_client
    quiz_id = "qid-fail"
    key = f"Quiz:u:{quiz_id}"
    r.setex(key, 3600, json.dumps({"status": "failed", "error": "LLM parse error"}))

    jr = client.get(f"/jobs/{quiz_id}", headers={"Authorization": "Bearer t"})
    assert jr.status_code == 200
    data = jr.json()
    assert data.get("status") == "failed"
    assert "error" in data


def test_submit_answers_returns_404_after_quiz_ttl_expiry(client):
    # Seed a quiz with very short TTL and let it expire
    r: redis.Redis = main_mod.redis_client
    quiz_id = "qid-expire"
    key = f"Quiz:u:{quiz_id}"
    r.setex(key, 1, json.dumps({"status": "done", "questions": ["Q1"]}))
    time.sleep(1.2)

    resp = client.post(
        "/submit-answers",
        json={"quiz_id": quiz_id, "answers": ["A1"]},
        headers={"Authorization": "Bearer t"},
    )
    assert resp.status_code == 404
