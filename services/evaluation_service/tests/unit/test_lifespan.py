from fastapi.testclient import TestClient
from services.evaluation_service import main as main_mod


def test_lifespan_starts_consumer_and_creates_tables(monkeypatch):
    called = {"db": 0, "consumer": 0}

    def fake_create():
        called["db"] += 1

    class FakeTask:
        def __init__(self):
            self.stop_event = type("E", (), {"set": lambda self: None})()

        def cancel(self):
            pass

    def fake_start_consumer():
        called["consumer"] += 1
        return FakeTask()

    monkeypatch.setattr(main_mod, "create_db_and_tables", fake_create)
    monkeypatch.setattr(main_mod, "start_consumer_task", fake_start_consumer)

    with TestClient(main_mod.app):
        pass

    assert called["db"] == 1
    assert called["consumer"] == 1
