import json
import pytest

from services.quizz_gen_service import generator_consumer as gc


class FakeRedis:
    def __init__(self):
        self.store = {}

    def setex(self, key, ttl, value):
        self.store[key] = value


class _ProcessContext:
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False


class FakeMessage:
    def __init__(self, payload):
        self.body = json.dumps(payload).encode("utf-8")

    def process(self, requeue=False):
        return _ProcessContext()


@pytest.mark.asyncio
async def test_handle_message_updates_quizz_job_key(monkeypatch):
    fake_redis = FakeRedis()
    monkeypatch.setattr(gc, "redis_client", fake_redis, raising=True)
    monkeypatch.setattr(
        gc,
        "quizz_generator",
        lambda topic, num_questions, difficulty, style: {
            "questions": ["Q1", "Q2"],
            "tags": [topic, difficulty],
        },
        raising=True,
    )
    monkeypatch.setattr(gc, "store_quizz", lambda **kwargs: None, raising=True)

    message = FakeMessage(
        {
            "quizz_id": "job-123",
            "username": "u",
            "topic": "linear algebra",
            "num_questions": 2,
            "difficulty": "easy",
            "style": "conceptual",
        }
    )

    await gc._handle_message(message)

    assert "Quizz:u:job-123" in fake_redis.store
    data = json.loads(fake_redis.store["Quizz:u:job-123"])
    assert data["status"] == "done"
    assert data["questions"] == ["Q1", "Q2"]
