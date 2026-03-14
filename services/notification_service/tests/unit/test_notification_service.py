import importlib
import json
import os
import sys
import types
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient


for key, value in {
    "RABBITMQ_URL": "amqp://guest:guest@localhost:5672/",
    "RESEND_API_KEY": "test-resend-key",
}.items():
    os.environ.setdefault(key, value)


resend_module = types.ModuleType("resend")


class _DummyEmails:
    @staticmethod
    def send(payload: dict) -> dict:
        return {"id": payload["to"][0]}


setattr(resend_module, "Emails", _DummyEmails)
sys.modules.setdefault("resend", resend_module)


consumer_mod = importlib.import_module("services.notification_service.consumer")
main_mod = importlib.import_module("services.notification_service.main")
data_models_mod = importlib.import_module("services.notification_service.data_models")

EmailRequest = data_models_mod.EmailRequest
EmailResponse = data_models_mod.EmailResponse


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


@pytest.mark.asyncio
async def test_handle_message_parses_payload_and_calls_email_handler(monkeypatch):
    handler_mock = AsyncMock()
    monkeypatch.setattr(
        consumer_mod, "handle_email_request", handler_mock, raising=True
    )

    await consumer_mod._handle_message(
        FakeMessage(
            {
                "to": "student@example.com",
                "subject": "Reminder",
                "html": "<p>Review algebra today.</p>",
            }
        )
    )

    handler_mock.assert_awaited_once()
    request_arg = handler_mock.await_args.args[0]
    assert isinstance(request_arg, EmailRequest)
    assert request_arg.to == "student@example.com"
    assert request_arg.subject == "Reminder"


@pytest.mark.asyncio
async def test_handle_email_request_calls_send_email(monkeypatch):
    send_email_mock = AsyncMock(
        return_value=EmailResponse(success=True, id="email_123")
    )
    monkeypatch.setattr(consumer_mod, "send_email", send_email_mock, raising=True)

    await consumer_mod.handle_email_request(
        EmailRequest(
            to="student@example.com",
            subject="Reminder",
            html="<p>Review algebra today.</p>",
        )
    )

    send_email_mock.assert_awaited_once()


@pytest.mark.asyncio
async def test_send_email_endpoint_returns_serialized_response(monkeypatch):
    async def _fake_send_email(email_request: EmailRequest) -> EmailResponse:
        _ = email_request
        return EmailResponse(success=True, id="sent-student@example.com")

    monkeypatch.setattr(main_mod, "send_email", _fake_send_email, raising=True)

    @asynccontextmanager
    async def _fake_lifespan(*args, **kwargs):
        yield

    main_mod.app.router.lifespan_context = _fake_lifespan

    async with AsyncClient(
        transport=ASGITransport(app=main_mod.app),
        base_url="http://testserver",
    ) as client:
        response = await client.post(
            "/send-email",
            json={
                "to": "student@example.com",
                "subject": "Reminder",
                "html": "<p>Review algebra today.</p>",
            },
        )

    assert response.status_code == 200
    assert response.json() == {
        "success": True,
        "id": "sent-student@example.com",
    }
