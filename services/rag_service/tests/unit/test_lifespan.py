from fastapi.testclient import TestClient
from services.rag_service import main as main_mod


def test_lifespan_calls_db_and_ingest(monkeypatch):
    called = {"db": 0, "ingest": 0}

    def fake_create():
        called["db"] += 1

    def fake_ingest():
        called["ingest"] += 1

    monkeypatch.setattr(main_mod, "create_db_and_tables", fake_create)
    monkeypatch.setattr(main_mod, "add_classes_and_embeddings", fake_ingest)

    with TestClient(main_mod.app):
        pass

    assert called["db"] == 1
    assert called["ingest"] == 1
