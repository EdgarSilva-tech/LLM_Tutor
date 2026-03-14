import importlib
import json
import os
import sys
import types
import uuid
from datetime import datetime
from unittest.mock import AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient
from pydantic import ValidationError
from sqlmodel import Session, SQLModel, create_engine, select


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


_ensure_opik_stub()

consumer_mod = importlib.import_module("services.learning_assessment_service.consumer")
persistence_mod = importlib.import_module(
    "services.learning_assessment_service.persistence"
)
data_models_mod = importlib.import_module(
    "services.learning_assessment_service.data_models"
)
main_mod = importlib.import_module("services.learning_assessment_service.main")

MasteryStore = data_models_mod.MasteryStore


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


@pytest.fixture
def mastery_engine(tmp_path, monkeypatch):
    engine = create_engine(
        f"sqlite:///{tmp_path / 'learning_assessment.db'}",
        connect_args={"check_same_thread": False},
    )
    SQLModel.metadata.create_all(engine, tables=[MasteryStore.__table__])
    monkeypatch.setattr(consumer_mod, "engine", engine, raising=True)
    monkeypatch.setattr(persistence_mod, "engine", engine, raising=True)
    return engine


def _store_mastery(engine, **overrides):
    payload = {
        "username": "alice",
        "topic": "fractions",
        "score": 0.4,
        "attempts": 1,
        "rolling_avg": 0.4,
        "last_quiz_id": str(uuid.uuid4()),
        "updated_at": datetime(2026, 3, 1, 9, 0, 0),
        "mastery_band": "low",
        "created_at": datetime(2026, 3, 1, 9, 0, 0),
        "status": "pending",
        "action_type": "quiz",
        "due_at": datetime(2026, 3, 8, 9, 0, 0),
    }
    payload.update(overrides)
    mastery = MasteryStore(**payload)
    with Session(engine) as session:
        session.add(mastery)
        session.commit()
        session.refresh(mastery)
    return mastery


def _freeze_consumer_now(monkeypatch, frozen_now: datetime) -> None:
    class FrozenDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            if tz is not None:
                return frozen_now.astimezone(tz)
            return frozen_now

    monkeypatch.setattr(consumer_mod, "datetime", FrozenDateTime, raising=True)


def test_build_fixed_schedule_uses_relative_offsets():
    frozen_now = datetime(2026, 3, 11, 12, 0, 0)

    schedule = consumer_mod._build_fixed_schedule(frozen_now)

    assert schedule == [
        ("reminder", datetime(2026, 3, 12, 12, 0, 0)),
        ("reminder", datetime(2026, 3, 14, 12, 0, 0)),
        ("quiz", datetime(2026, 3, 18, 12, 0, 0)),
    ]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("scores", "expected_band"),
    [
        ([0.5], "low"),
        ([0.6], "medium"),
        ([0.8], "high"),
    ],
)
async def test_handle_message_persists_fixed_schedule_and_calls_adviser(
    mastery_engine, monkeypatch, scores, expected_band
):
    adviser_mock = AsyncMock()
    notification_mock = AsyncMock()
    monkeypatch.setattr(
        consumer_mod, "handle_learning_assessment", adviser_mock, raising=True
    )
    monkeypatch.setattr(
        consumer_mod,
        "publish_notification_email_request",
        notification_mock,
        raising=True,
    )
    assessment_id = uuid.uuid4()
    frozen_now = datetime(2026, 3, 11, 12, 0, 0)
    _freeze_consumer_now(monkeypatch, frozen_now)

    await consumer_mod._handle_message(
        FakeMessage(
            {
                "username": f"user-{expected_band}",
                "email": f"user-{expected_band}@example.com",
                "assessment_id": str(assessment_id),
                "quizz_questions": ["Q1"],
                "student_answers": ["A1"],
                "correct_answers": ["C1"],
                "topic": "fractions",
                "scores": scores,
                "feedback": [{"message": "keep going"}],
            }
        )
    )

    with Session(mastery_engine) as session:
        rows = session.exec(
            select(MasteryStore)
            .where(MasteryStore.last_quiz_id == str(assessment_id))
            .order_by(MasteryStore.due_at)
        ).all()

    assert len(rows) == 3
    assert [row.action_type for row in rows] == [
        "reminder",
        "reminder",
        "quiz",
    ]
    assert [row.due_at for row in rows] == [
        datetime(2026, 3, 12, 12, 0, 0),
        datetime(2026, 3, 14, 12, 0, 0),
        datetime(2026, 3, 18, 12, 0, 0),
    ]
    assert notification_mock.await_count == 2
    first_payload = notification_mock.await_args_list[0].args[0]
    second_payload = notification_mock.await_args_list[1].args[0]
    assert first_payload["to"] == f"user-{expected_band}@example.com"
    assert first_payload["subject"] == "Study reminder 1: review fractions"
    assert first_payload["scheduled_at"] == "2026-03-12T12:00:00"
    assert second_payload["subject"] == "Study reminder 2: review fractions"
    assert second_payload["scheduled_at"] == "2026-03-14T12:00:00"
    assert notification_mock.await_args_list[0].kwargs["delay"] == 86400000
    assert notification_mock.await_args_list[1].kwargs["delay"] == 259200000

    for row in rows:
        assert row.username == f"user-{expected_band}"
        assert row.topic == "fractions"
        assert row.score == sum(scores)
        assert row.attempts == 1
        assert row.rolling_avg == sum(scores)
        assert row.mastery_band == expected_band
        assert row.status == "pending"
        assert row.created_at == frozen_now
        assert row.updated_at == frozen_now

    adviser_mock.assert_awaited_once()
    message_arg = adviser_mock.await_args.args[0]
    assert message_arg.username == f"user-{expected_band}"
    assert message_arg.assessment_id == str(assessment_id)
    assert message_arg.scores == scores


@pytest.mark.asyncio
async def test_handle_message_uses_existing_attempt_count_for_same_user_and_topic(
    mastery_engine, monkeypatch
):
    adviser_mock = AsyncMock()
    notification_mock = AsyncMock()
    monkeypatch.setattr(
        consumer_mod, "handle_learning_assessment", adviser_mock, raising=True
    )
    monkeypatch.setattr(
        consumer_mod,
        "publish_notification_email_request",
        notification_mock,
        raising=True,
    )
    _store_mastery(mastery_engine, action_type="reminder")
    _store_mastery(mastery_engine)
    _store_mastery(mastery_engine, username="alice", topic="geometry")
    _store_mastery(mastery_engine, username="bob", topic="fractions")

    assessment_id = uuid.uuid4()
    _freeze_consumer_now(monkeypatch, datetime(2026, 3, 11, 15, 30, 0))
    await consumer_mod._handle_message(
        FakeMessage(
            {
                "username": "alice",
                "email": "alice@example.com",
                "assessment_id": str(assessment_id),
                "quizz_questions": ["Q1"],
                "student_answers": ["A1"],
                "correct_answers": ["C1"],
                "topic": "fractions",
                "scores": [0.75],
                "feedback": [{"message": "review equivalent fractions"}],
            }
        )
    )

    with Session(mastery_engine) as session:
        rows = session.exec(
            select(MasteryStore)
            .where(MasteryStore.last_quiz_id == str(assessment_id))
            .order_by(MasteryStore.due_at)
        ).all()

    assert len(rows) == 3
    for row in rows:
        assert row.attempts == 2
        assert row.rolling_avg == pytest.approx(0.375)
        assert row.mastery_band == "medium"
    assert notification_mock.await_count == 2
    adviser_mock.assert_awaited_once()


@pytest.mark.asyncio
async def test_handle_message_invalid_payload_does_not_persist_rows(
    mastery_engine, monkeypatch
):
    adviser_mock = AsyncMock()
    notification_mock = AsyncMock()
    monkeypatch.setattr(
        consumer_mod, "handle_learning_assessment", adviser_mock, raising=True
    )
    monkeypatch.setattr(
        consumer_mod,
        "publish_notification_email_request",
        notification_mock,
        raising=True,
    )

    with pytest.raises(ValidationError):
        await consumer_mod._handle_message(
            FakeMessage(
                {
                    "username": "alice",
                    "assessment_id": "assessment-123",
                    "quizz_questions": ["Q1"],
                    "student_answers": ["A1"],
                    "correct_answers": ["C1"],
                    "topic": "fractions",
                    "scores": "invalid-scores",
                    "feedback": [{"message": "invalid"}],
                }
            )
        )

    with Session(mastery_engine) as session:
        rows = session.exec(select(MasteryStore)).all()

    assert rows == []
    adviser_mock.assert_not_awaited()
    notification_mock.assert_not_awaited()


@pytest.mark.asyncio
async def test_handle_message_without_email_skips_notification_publish(
    mastery_engine, monkeypatch
):
    adviser_mock = AsyncMock()
    notification_mock = AsyncMock()
    monkeypatch.setattr(
        consumer_mod, "handle_learning_assessment", adviser_mock, raising=True
    )
    monkeypatch.setattr(
        consumer_mod,
        "publish_notification_email_request",
        notification_mock,
        raising=True,
    )
    assessment_id = uuid.uuid4()
    _freeze_consumer_now(monkeypatch, datetime(2026, 3, 11, 12, 0, 0))

    await consumer_mod._handle_message(
        FakeMessage(
            {
                "username": "eve",
                "assessment_id": str(assessment_id),
                "quizz_questions": ["Q1"],
                "student_answers": ["A1"],
                "correct_answers": ["C1"],
                "topic": "fractions",
                "scores": [0.5],
                "feedback": [{"message": "review basics"}],
            }
        )
    )

    notification_mock.assert_not_awaited()
    adviser_mock.assert_awaited_once()


def test_get_learning_assessment_mastery_by_username_returns_due_dates_and_statuses(
    mastery_engine,
):
    reminder_2 = _store_mastery(
        mastery_engine,
        username="carol",
        topic="algebra",
        score=0.8,
        attempts=3,
        rolling_avg=0.6,
        mastery_band="high",
        status="sent",
        action_type="reminder",
        due_at=datetime(2026, 3, 14, 9, 0, 0),
    )
    reminder_1 = _store_mastery(
        mastery_engine,
        username="carol",
        topic="algebra",
        score=0.8,
        attempts=3,
        rolling_avg=0.6,
        mastery_band="high",
        status="pending",
        action_type="reminder",
        due_at=datetime(2026, 3, 12, 9, 0, 0),
    )
    quiz = _store_mastery(
        mastery_engine,
        username="carol",
        topic="algebra",
        score=0.8,
        attempts=3,
        rolling_avg=0.6,
        mastery_band="high",
        status="completed",
        action_type="quiz",
        due_at=datetime(2026, 3, 18, 9, 0, 0),
    )

    result = persistence_mod.get_learning_assessment_mastery_by_username("carol")

    assert result["username"] == "carol"
    assert [row["id"] for row in result["schedule"]] == [
        reminder_1.id,
        reminder_2.id,
        quiz.id,
    ]
    assert [row["action_type"] for row in result["schedule"]] == [
        "reminder",
        "reminder",
        "quiz",
    ]
    assert [row["due_at"] for row in result["schedule"]] == [
        datetime(2026, 3, 12, 9, 0, 0),
        datetime(2026, 3, 14, 9, 0, 0),
        datetime(2026, 3, 18, 9, 0, 0),
    ]
    assert [row["status"] for row in result["schedule"]] == [
        "pending",
        "sent",
        "completed",
    ]
    assert all(row["topic"] == "algebra" for row in result["schedule"])
    assert all(row["attempts"] == 3 for row in result["schedule"])
    assert all(row["mastery_band"] == "high" for row in result["schedule"])


@pytest.mark.asyncio
async def test_get_learning_assessment_mastery_endpoint_returns_serialized_schedule(
    mastery_engine,
):
    reminder = _store_mastery(
        mastery_engine,
        username="dora",
        topic="geometry",
        score=0.7,
        attempts=2,
        rolling_avg=0.65,
        mastery_band="medium",
        status="queued",
        action_type="reminder",
        due_at=datetime(2026, 3, 12, 11, 30, 0),
        updated_at=datetime(2026, 3, 11, 8, 0, 0),
        created_at=datetime(2026, 3, 11, 8, 0, 0),
    )
    quiz = _store_mastery(
        mastery_engine,
        username="dora",
        topic="geometry",
        score=0.7,
        attempts=2,
        rolling_avg=0.65,
        mastery_band="medium",
        status="pending",
        action_type="quiz",
        due_at=datetime(2026, 3, 18, 11, 30, 0),
        updated_at=datetime(2026, 3, 11, 8, 0, 0),
        created_at=datetime(2026, 3, 11, 8, 0, 0),
    )

    async with AsyncClient(
        transport=ASGITransport(app=main_mod.app),
        base_url="http://testserver",
    ) as client:
        response = await client.get("/learning-assessment/dora/mastery")

    assert response.status_code == 200
    assert response.json() == {
        "username": "dora",
        "schedule": [
            {
                "id": str(reminder.id),
                "topic": "geometry",
                "score": 0.7,
                "attempts": 2,
                "rolling_avg": 0.65,
                "last_quiz_id": str(reminder.last_quiz_id),
                "updated_at": "2026-03-11T08:00:00",
                "mastery_band": "medium",
                "created_at": "2026-03-11T08:00:00",
                "status": "queued",
                "action_type": "reminder",
                "due_at": "2026-03-12T11:30:00",
            },
            {
                "id": str(quiz.id),
                "topic": "geometry",
                "score": 0.7,
                "attempts": 2,
                "rolling_avg": 0.65,
                "last_quiz_id": str(quiz.last_quiz_id),
                "updated_at": "2026-03-11T08:00:00",
                "mastery_band": "medium",
                "created_at": "2026-03-11T08:00:00",
                "status": "pending",
                "action_type": "quiz",
                "due_at": "2026-03-18T11:30:00",
            },
        ],
    }
