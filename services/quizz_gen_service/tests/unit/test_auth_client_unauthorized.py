import pytest
import httpx

from services.quizz_gen_service.auth_client import get_current_user_from_auth_service
from fastapi import HTTPException


@pytest.mark.asyncio
async def test_auth_client_unauthorized_raises_401(monkeypatch):
    token = "bad-token"

    async def fake_get(self, url, *args, **kwargs):
        return httpx.Response(401, request=httpx.Request("GET", url))

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get, raising=True)

    with pytest.raises(HTTPException) as exc:
        await get_current_user_from_auth_service(token)
    assert exc.value.status_code == 401
