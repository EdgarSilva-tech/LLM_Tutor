import os
import json
import asyncio
import pytest
import redis
from fastapi.testclient import TestClient

from services.quizz_gen_service import main as main_mod
from services.quizz_gen_service.data_models import User
from services.quizz_gen_service.quizz_settings import quizz_settings


pytestmark = pytest.mark.integration


@pytest.fixture(autouse=True)
def _setup_env_and_redis(monkeypatch):
    # Point Redis to local test instance (CI provides redis:7-alpine on 6379)
    os.environ["REDIS_ENDPOINT"] = quizz_settings.REDIS_ENDPOINT
    os.environ["REDIS_PORT"] = str(quizz_settings.REDIS_PORT)
    # Build a real Redis client (no auth for local)
    r = redis.Redis(
        host=quizz_settings.REDIS_ENDPOINT,
        username=quizz_settings.REDIS_USERNAME,
        password=quizz_settings.REDIS_PASSWORD,
        port=quizz_settings.REDIS_PORT,
        decode_responses=True,
        socket_connect_timeout=2,
        socket_timeout=2,
        health_check_interval=10,
    )
    # Ensure clean slate for the test user prefix
    for k in list(r.scan_iter("quizz_request:u:*")):
        r.delete(k)
    for k in list(r.scan_iter("Quiz:u:*")):
        r.delete(k)
    # Inject into app
    monkeypatch.setattr(main_mod, "redis_client", r)
    yield
    # Cleanup
    for k in list(r.scan_iter("quizz_request:u:*")):
        r.delete(k)
    for k in list(r.scan_iter("Quiz:u:*")):
        r.delete(k)


@pytest.fixture()
def client(monkeypatch):
    # Bypass real auth-service call
    async def _fake_user():
        return User(username="u", email="e@example.com", disabled=False)

    app = main_mod.app
    app.dependency_overrides[main_mod.get_current_active_user] = _fake_user
    return TestClient(app)


def test_generate_quiz_caches_and_returns_questions_integration(client, monkeypatch):
    questions = ["Q1", "Q2", "Q3"]
    # Avoid hitting real LLM
    monkeypatch.setattr(main_mod, "quizz_generator", lambda *a, **k: questions)

    body = {
        "topic": "algebra",
        "num_questions": 3,
        "difficulty": "easy",
        "style": "conceptual",
    }
    resp = client.post(
        "/generate-quiz",
        json=body,
        headers={"Authorization": "Bearer t"},
    )
    assert resp.status_code == 200
    assert resp.json() == {"quizz_questions": questions}

    # Verify cache written
    r: redis.Redis = main_mod.redis_client
    quizz_str = json.dumps({"questions": questions}, sort_keys=True)
    import hashlib

    quizz_hash = hashlib.sha256(quizz_str.encode()).hexdigest()
    key = f"quizz_request:u:{quizz_hash}"
    assert r.get(key) == quizz_str


def test_create_quiz_sets_redis_and_submit_answers_publishes_bg(client, monkeypatch):
    questions = ["A", "B"]
    # Stub generator
    monkeypatch.setattr(main_mod, "quizz_generator", lambda *a, **k: questions)

    # Stub publisher to avoid real RabbitMQ in integration test
    async def _noop_publish(payload):
        await asyncio.sleep(0)  # simulate async
        return None

    # Patch internal _publish_with_retry used by submit_answers background task
    from services.quizz_gen_service import mq as mq_mod

    monkeypatch.setattr(mq_mod, "_publish_with_retry", _noop_publish)

    # Create quiz (writes to Redis)
    body = {
        "topic": "probability",
        "num_questions": 2,
        "difficulty": "easy",
        "style": "conceptual",
    }
    r = client.post(
        "/create-quiz",
        json=body,
        headers={"Authorization": "Bearer t"},
    )
    assert r.status_code == 200
    data = r.json()
    assert "quiz_id" in data and data["questions"] == questions

    quiz_id = data.get("id") or data["quiz_id"]

    # Now submit answers; should return 202 and enqueue background publish
    sr = client.post(
        "/submit-answers",
        json={"quiz_id": quiz_id, "answers": ["x", "y"]},
        headers={"Authorization": "Bearer t"},
    )
    assert sr.status_code == 202
    sj = sr.json()
    assert "job_id" in sj
