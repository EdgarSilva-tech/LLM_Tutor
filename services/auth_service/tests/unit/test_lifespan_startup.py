from fastapi.testclient import TestClient
from services.auth_service import main as main_mod


def test_lifespan_calls_create_db_and_tables(monkeypatch):
    called = {"n": 0}

    def _fake_create():
        called["n"] += 1

    monkeypatch.setattr(main_mod, "create_db_and_tables", _fake_create)

    # Usar context manager garante chamada de startup/shutdown
    with TestClient(main_mod.app) as _:
        pass

    assert called["n"] == 1
