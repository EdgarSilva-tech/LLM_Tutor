import hashlib
import json
import pytest
from fastapi.testclient import TestClient

from services.quizz_gen_service import main as main_mod
from services.quizz_gen_service.data_models import User


class FakeRedis:
    def __init__(self):
        self.store = {}

    def set(self, key, value):
        self.store[key] = value

    def setex(self, key, ttl, value):
        self.store[key] = value

    def get(self, key):
        return self.store.get(key)


@pytest.fixture(autouse=True)
def fake_redis(monkeypatch):
    r = FakeRedis()
    monkeypatch.setattr(main_mod, "redis_client", r)
    return r


@pytest.fixture
def client(monkeypatch):
    app = main_mod.app

    async def _fake_user():
        return User(username="u", email="e", disabled=False)

    app.dependency_overrides[main_mod.get_current_active_user] = _fake_user
    return TestClient(app)


def test_generate_quiz_caches_and_returns_questions(client, fake_redis, monkeypatch):
    questions = {"questions": ["Q1", "Q2"], "tags": ["t1", "t2"]}
    monkeypatch.setattr(main_mod, "quizz_generator", lambda *a, **k: questions)

    body = {
        "topic": "t",
        "num_questions": 2,
        "difficulty": "easy",
        "style": "conceptual",
    }
    resp = client.post(
        "/generate-quiz", json=body, headers={"Authorization": "Bearer t"}
    )
    assert resp.status_code == 200
    assert resp.json() == {
        "quizz_questions": questions["questions"],
        "tags": questions["tags"],
    }

    # Verifica chave no Redis com o hash esperado
    quizz_str = json.dumps(
        {"questions": questions["questions"], "tags": questions["tags"]}, sort_keys=True
    )
    quizz_hash = hashlib.sha256(quizz_str.encode()).hexdigest()
    key = f"quizz_request:u:{quizz_hash}"
    assert key in fake_redis.store
    assert fake_redis.store[key] == quizz_str


def test_create_quiz_sets_redis_and_returns_id(client, fake_redis, monkeypatch):
    questions = {"questions": ["Q1", "Q2", "Q3"], "tags": ["t1", "t2", "t3"]}
    monkeypatch.setattr(main_mod, "quizz_generator", lambda *a, **k: questions)

    body = {
        "topic": "t",
        "num_questions": 3,
        "difficulty": "easy",
        "style": "conceptual",
    }
    resp = client.post("/create-quiz", json=body, headers={"Authorization": "Bearer t"})
    assert resp.status_code == 200
    data = resp.json()
    assert "quizz_id" in data and "questions" in data
    assert data["questions"] == questions["questions"]

    key = f"Quizz:u:{data['quizz_id']}"
    assert key in fake_redis.store
    # valor guardado é json.dumps(questions)
    assert fake_redis.store[key] == json.dumps(questions)
