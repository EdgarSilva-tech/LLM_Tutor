import importlib
import json
import os
import sys
import types
from datetime import datetime
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, create_engine, select


for key, value in {
    "OPENAI_API_KEY": "test-openai-key",
    "OPIK_API_KEY": "test-opik-key",
    "REDIS_ENDPOINT": "localhost",
    "REDIS_PASSWORD": "password",
    "SECRET_KEY": "secret",
    "RABBITMQ_URL": "amqp://guest:guest@localhost:5672/",
    "DB_NAME": "test_db",
    "DB_PORT": "5432",
    "PG_PASSWORD": "postgres",
    "USERNAME": "tester",
    "HOST": "localhost",
    "RABBITMQ_USER": "guest",
    "RABBITMQ_PASS": "guest",
    "RESEND_API_KEY": "test-resend-key",
}.items():
    os.environ.setdefault(key, value)


def _ensure_opik_stub() -> None:
    try:
        import opik.integrations.langchain  # noqa: F401
    except ModuleNotFoundError:
        opik_module = types.ModuleType("opik")
        integrations_module = types.ModuleType("opik.integrations")
        langchain_module = types.ModuleType("opik.integrations.langchain")

        class DummyTracer:
            def __init__(self, *args, **kwargs):
                self.args = args
                self.kwargs = kwargs

        setattr(langchain_module, "OpikTracer", DummyTracer)
        sys.modules["opik"] = opik_module
        sys.modules["opik.integrations"] = integrations_module
        sys.modules["opik.integrations.langchain"] = langchain_module


def _ensure_resend_stub() -> None:
    resend_module = types.ModuleType("resend")

    class DummyEmails:
        @staticmethod
        def send(payload: dict) -> dict:
            return {"id": payload["to"][0]}

    setattr(resend_module, "Emails", DummyEmails)
    sys.modules.setdefault("resend", resend_module)


_ensure_opik_stub()
_ensure_resend_stub()

eval_main_mod = importlib.import_module("services.evaluation_service.main")
eval_data_models_mod = importlib.import_module("services.evaluation_service.data_models")
la_consumer_mod = importlib.import_module("services.learning_assessment_service.consumer")
la_persistence_mod = importlib.import_module(
    "services.learning_assessment_service.persistence"
)
la_data_models_mod = importlib.import_module(
    "services.learning_assessment_service.data_models"
)
notification_consumer_mod = importlib.import_module(
    "services.notification_service.consumer"
)

MasteryStore = la_data_models_mod.MasteryStore
User = eval_data_models_mod.User


class FakeRedis:
    def __init__(self):
        self.store = {}

    def get(self, key):
        return self.store.get(key)

    def set(self, key, value):
        self.store[key] = value


class _ProcessContext:
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False


class FakeMessage:
    def __init__(self, payload: dict):
        self.body = json.dumps(payload).encode("utf-8")

    def process(self, requeue=False):
        return _ProcessContext()


def _freeze_consumer_now(monkeypatch, frozen_now: datetime) -> None:
    class FrozenDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            if tz is not None:
                return frozen_now.astimezone(tz)
            return frozen_now

    monkeypatch.setattr(la_consumer_mod, "datetime", FrozenDateTime, raising=True)


@pytest.fixture
def client_with_user(monkeypatch):
    async def _fake_user():
        return User(
            username="u",
            email="u@example.com",
            full_name="User",
            disabled=False,
        )

    eval_main_mod.app.dependency_overrides[
        eval_main_mod.get_current_active_user
    ] = _fake_user
    yield TestClient(eval_main_mod.app)
    eval_main_mod.app.dependency_overrides.clear()


@pytest.fixture
def mastery_engine(tmp_path, monkeypatch):
    engine = create_engine(
        f"sqlite:///{tmp_path / 'learning_assessment_flow.db'}",
        connect_args={"check_same_thread": False},
    )
    SQLModel.metadata.create_all(engine, tables=[MasteryStore.__table__])
    monkeypatch.setattr(la_consumer_mod, "engine", engine, raising=True)
    monkeypatch.setattr(la_persistence_mod, "engine", engine, raising=True)
    return engine


@pytest.mark.asyncio
async def test_evaluation_to_learning_assessment_to_notification_reminder_flow(
    client_with_user, mastery_engine, monkeypatch
):
    redis = FakeRedis()
    monkeypatch.setattr(eval_main_mod, "redis_client", redis)
    monkeypatch.setattr(
        eval_main_mod,
        "store_evals",
        lambda username, q, a, correct, score, feedback: None,
    )

    class AIMessage:
        def __init__(self, content):
            self.content = content

    monkeypatch.setattr(
        eval_main_mod,
        "eval_answer",
        lambda question, answer: AIMessage(
            json.dumps(
                {
                    "correct_answer": "42",
                    "score": 0.5,
                    "feedback": "review arithmetic basics",
                }
            )
        ),
    )

    published_events: list[dict] = []
    monkeypatch.setattr(
        eval_main_mod,
        "publish_evaluation_completed_sync",
        lambda payload: published_events.append(payload),
    )

    adviser_mock = AsyncMock()
    reminder_publish_mock = AsyncMock()
    monkeypatch.setattr(
        la_consumer_mod, "handle_learning_assessment", adviser_mock, raising=True
    )
    monkeypatch.setattr(
        la_consumer_mod,
        "publish_notification_email_request",
        reminder_publish_mock,
        raising=True,
    )
    _freeze_consumer_now(monkeypatch, datetime(2026, 3, 11, 12, 0, 0))

    response = client_with_user.post(
        "/eval-service",
        json={
            "student_id": "u",
            "topic": "arithmetic",
            "quizz_questions": ["What is 6 * 7?"],
            "student_answers": ["36"],
        },
        headers={"Authorization": "Bearer test-token"},
    )

    assert response.status_code == 200
    assert len(published_events) == 1
    event_payload = published_events[0]
    assert event_payload["username"] == "u"
    assert event_payload["email"] == "u@example.com"
    assert event_payload["topic"] == "arithmetic"
    assert event_payload["scores"] == [0.5]

    await la_consumer_mod._handle_message(FakeMessage(event_payload))

    with Session(mastery_engine) as session:
        rows = session.exec(
            select(MasteryStore)
            .where(MasteryStore.last_quiz_id == event_payload["assessment_id"])
            .order_by(MasteryStore.due_at)
        ).all()

    assert len(rows) == 3
    assert [row.action_type for row in rows] == ["reminder", "reminder", "quiz"]
    assert reminder_publish_mock.await_count == 2

    first_reminder_payload = reminder_publish_mock.await_args_list[0].args[0]
    assert first_reminder_payload["to"] == "u@example.com"
    assert first_reminder_payload["subject"] == "Study reminder 1: review arithmetic"
    assert first_reminder_payload["scheduled_at"] == "2026-03-12T12:00:00"
    assert reminder_publish_mock.await_args_list[0].kwargs["delay"] == 86400000
    adviser_mock.assert_awaited_once()

    send_email_mock = AsyncMock()
    monkeypatch.setattr(
        notification_consumer_mod, "send_email", send_email_mock, raising=True
    )

    await notification_consumer_mod._handle_message(
        FakeMessage(first_reminder_payload)
    )

    send_email_mock.assert_awaited_once()
    email_request = send_email_mock.await_args.args[0]
    assert email_request.to == "u@example.com"
    assert email_request.subject == "Study reminder 1: review arithmetic"
    assert "arithmetic" in email_request.html

