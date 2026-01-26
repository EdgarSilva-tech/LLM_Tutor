import pytest
import redis
from fastapi.testclient import TestClient

from services.rag_service import main as rag_main
from services.rag_service.rag_settings import rag_settings
from services.rag_service.data_models import User


pytestmark = pytest.mark.integration


@pytest.fixture(autouse=True)
def _wire_local_redis(monkeypatch):
    # Build a real Redis client using configured endpoint (CI sets secrets)
    r = redis.Redis(
        host=rag_settings.REDIS_ENDPOINT,
        port=rag_settings.REDIS_PORT,
        username=rag_settings.REDIS_USERNAME,
        password=rag_settings.REDIS_PASSWORD,
        decode_responses=True,
        socket_connect_timeout=2,
        socket_timeout=2,
        health_check_interval=10,
    )
    # Replace global client exposed by the module
    monkeypatch.setattr(rag_main, "redis_client", r, raising=True)
    yield


@pytest.fixture(autouse=True)
def _disable_db_and_ingest(monkeypatch):
    # Prevent connecting to Postgres during app startup and requests
    monkeypatch.setattr(rag_main, "create_db_and_tables", lambda: None, raising=True)
    monkeypatch.setattr(
        rag_main, "add_classes_and_embeddings", lambda: None, raising=True
    )

    class _DummySession:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def exec(self, *args, **kwargs):
            return []

    monkeypatch.setattr(rag_main, "Session", _DummySession, raising=True)


@pytest.fixture()
def client(monkeypatch):
    # Stub LLM to avoid network
    class _LLM:
        def invoke(self, prompt, config=None):
            class _R:
                content = "This is an answer."

            return _R()

    def _fake_get_llm(*args, **kwargs):
        return _LLM()

    from services.rag_service import rag_utils

    monkeypatch.setattr(rag_utils, "get_llm", _fake_get_llm)

    app = rag_main.app

    # Bypass auth by overriding dependency
    async def _fake_user():
        return User(username="u", email="u@example.com", full_name="U", disabled=False)

    app.dependency_overrides[rag_main.get_current_active_user] = _fake_user
    return TestClient(app)


def test_question_answer_returns_answer_and_context(client):
    payload = {"question": "What is a vector space?", "top_k": 2}
    res = client.post("/question-answer", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "answer" in data and "context" in data


def test_question_answer_error_path_returns_500(monkeypatch):
    # Force the LLM call to raise inside question_answer flow
    class _LLM:
        def invoke(self, prompt, config=None):
            raise RuntimeError("LLM failed")

    def _fake_get_llm(*args, **kwargs):
        return _LLM()

    from services.rag_service import rag_utils

    monkeypatch.setattr(rag_utils, "get_llm", _fake_get_llm)
    app = rag_main.app
    with TestClient(app) as c:
        res = c.post("/question-answer", json={"question": "X", "top_k": 1})
        assert res.status_code == 500
        assert "RAG error" in res.json().get("detail", "")


def test_embed_returns_embedding_and_caches(monkeypatch):
    # Patch embeddings used by app to deterministic vector
    class _Emb:
        @staticmethod
        def embed_query(text):
            return [0.11, 0.22, 0.33]

    monkeypatch.setattr(rag_main, "embeddings", _Emb())
    with TestClient(rag_main.app) as c:
        payload = {"text": "hello"}
        res = c.post("/embed", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data.get("embedding") == [0.11, 0.22, 0.33]


def test_search_returns_results(monkeypatch):
    # Patch embeddings to deterministic vector
    class _Emb:
        @staticmethod
        def embed_query(text):
            return [0.5, 0.4, 0.3]

    monkeypatch.setattr(rag_main, "embeddings", _Emb())
    with TestClient(rag_main.app) as c:
        res = c.get("/search", params={"text": "query", "top_k": 2})
        assert res.status_code == 200
        body = res.json()
        assert "results" in body
        assert isinstance(body["results"], list)
