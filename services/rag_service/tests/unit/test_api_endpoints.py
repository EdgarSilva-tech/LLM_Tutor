import json
import uuid
import pytest
from fastapi.testclient import TestClient

from services.rag_service import main as main_mod
from services.rag_service.data_models import User


class FakeRedis:
    def __init__(self):
        self.store = {}

    def get(self, key):
        return self.store.get(key)

    def set(self, key, value):
        self.store[key] = value


class FakeSession:
    def __init__(self, results):
        self._results = results

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def exec(self, _statement):
        # devolve um iterável de resultados simulados
        return self._results


class FakeRow:
    def __init__(self, content, chunk_index=0, lesson_id=None):
        self.content = content
        self.chunk_index = chunk_index
        self.lesson_id = lesson_id or uuid.uuid4()


@pytest.fixture(autouse=True)
def client_with_user(monkeypatch):
    # Override auth para endpoints
    async def _fake_user():
        return User(username="u", email="e", full_name="U", disabled=False)

    main_mod.app.dependency_overrides[main_mod.get_current_active_user] = _fake_user
    return TestClient(main_mod.app)


def test_health_ok(client_with_user):
    resp = client_with_user.get("/health")
    assert resp.status_code == 200
    assert resp.json()["service"] == "RAG Service"


def test_question_answer_redis_miss_then_ok(client_with_user, monkeypatch):
    # Redis miss -> chama embeddings.embed_query e grava cache; Session devolve contexto; question_answer devolve AIMessage-like
    r = FakeRedis()
    monkeypatch.setattr(main_mod, "redis_client", r)

    class Emb:
        @staticmethod
        def embed_query(text):
            return [0.1, 0.2, 0.3]

    monkeypatch.setattr(main_mod, "embeddings", Emb)

    # Session fake com 2 conteúdos
    fake_results = [FakeRow("C1", 0), FakeRow("C2", 1)]
    monkeypatch.setattr(main_mod, "Session", lambda engine: FakeSession(fake_results))

    class Resp:
        def __init__(self, content):
            self.content = content

    def fake_qa(question, context):
        return Resp("ans")

    monkeypatch.setattr(main_mod, "question_answer", fake_qa)

    body = {"question": "Q?", "top_k": 2}
    resp = client_with_user.post(
        "/question-answer", json=body, headers={"Authorization": "Bearer t"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["answer"] == "ans"
    assert data["context"] == ["C1", "C2"]
    # cache foi setado com a pergunta como chave
    assert "Q?" in r.store


def test_question_answer_redis_hit_path(client_with_user, monkeypatch):
    r = FakeRedis()
    r.set("QHIT", json.dumps([0.5, 0.5]))
    monkeypatch.setattr(main_mod, "redis_client", r)

    # não deve chamar embeddings; ainda assim Session devolve contexto
    fake_results = [FakeRow("CX")]
    monkeypatch.setattr(main_mod, "Session", lambda engine: FakeSession(fake_results))
    monkeypatch.setattr(main_mod, "question_answer", lambda q, c: "A")

    body = {"question": "QHIT", "top_k": 1}
    resp = client_with_user.post(
        "/question-answer", json=body, headers={"Authorization": "Bearer t"}
    )
    assert resp.status_code == 200
    assert resp.json()["context"] == ["CX"]


def test_question_answer_error_returns_500(client_with_user, monkeypatch):
    r = FakeRedis()
    monkeypatch.setattr(main_mod, "redis_client", r)
    monkeypatch.setattr(main_mod, "Session", lambda engine: FakeSession([FakeRow("C")]))

    def boom(*a, **k):
        raise RuntimeError("llm error")

    monkeypatch.setattr(main_mod, "question_answer", boom)

    body = {"question": "Q", "top_k": 1}
    resp = client_with_user.post(
        "/question-answer", json=body, headers={"Authorization": "Bearer t"}
    )
    assert resp.status_code == 500


def test_embed_cache_miss_and_hit(client_with_user, monkeypatch):
    r = FakeRedis()
    monkeypatch.setattr(main_mod, "redis_client", r)

    class Emb:
        @staticmethod
        def embed_query(text):
            return [0.7, 0.8]

    monkeypatch.setattr(main_mod, "embeddings", Emb)

    # Miss -> gera e guarda sob "u_text"
    body = {"text": "hello"}
    resp = client_with_user.post(
        "/embed", json=body, headers={"Authorization": "Bearer t"}
    )
    assert resp.status_code == 200
    assert resp.json()["embedding"] == [0.7, 0.8]
    assert r.store["u_hello"] == json.dumps([0.7, 0.8])

    # Hit -> se guardarmos em key "hello", endpoint deve ler e retornar sem gerar novamente
    r.set("hello", json.dumps([1.0]))
    resp2 = client_with_user.post(
        "/embed", json=body, headers={"Authorization": "Bearer t"}
    )
    assert resp2.status_code == 200
    assert resp2.json()["embedding"] == [1.0]


def test_search_success_cache_miss(client_with_user, monkeypatch):
    r = FakeRedis()
    monkeypatch.setattr(main_mod, "redis_client", r)

    class Emb:
        @staticmethod
        def embed_query(text):
            return [0.2]

    monkeypatch.setattr(main_mod, "embeddings", Emb)

    fake_results = [FakeRow("A", 3), FakeRow("B", 4)]
    monkeypatch.setattr(main_mod, "Session", lambda engine: FakeSession(fake_results))

    resp = client_with_user.get(
        "/search",
        params={"text": "t", "top_k": 2},
        headers={"Authorization": "Bearer t"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["query"] == "t"
    assert len(body["results"]) == 2
    assert r.store["u_t"] == json.dumps([0.2])


def test_search_error_returns_500(client_with_user, monkeypatch):
    r = FakeRedis()
    monkeypatch.setattr(main_mod, "redis_client", r)

    class Emb:
        @staticmethod
        def embed_query(text):
            return [0.2]

    monkeypatch.setattr(main_mod, "embeddings", Emb)

    # FakeSession levanta erro ao exec
    class BadSession(FakeSession):
        def exec(self, _):
            raise RuntimeError("db error")

    monkeypatch.setattr(main_mod, "Session", lambda engine: BadSession([]))

    resp = client_with_user.get(
        "/search", params={"text": "t"}, headers={"Authorization": "Bearer t"}
    )
    assert resp.status_code == 500
