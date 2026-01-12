import time
import httpx
import pytest

from services.quizz_gen_service.auth_client import (
    get_current_user_from_auth_service,
)
from services.quizz_gen_service.data_models import User
from fastapi import HTTPException
from services.quizz_gen_service import auth_client as ac


@pytest.mark.asyncio
async def test_auth_cache_hit_and_timeout(monkeypatch):
    token = "token-abc"

    # diminui TTL para teste de expiração
    monkeypatch.setattr(
        "services.quizz_gen_service.auth_client._TOKEN_CACHE_TTL_SECONDS", 30
    )

    user_payload = {"username": "u", "email": "e", "disabled": False}

    calls = {"n": 0}

    async def fake_get(self, url, *args, **kwargs):
        calls["n"] += 1
        if calls["n"] == 1:
            return httpx.Response(
                200, json=user_payload, request=httpx.Request("GET", url)
            )
        # chamadas subsequentes simulam timeout
        raise httpx.ConnectTimeout("timeout")

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get, raising=True)

    # primeira chamada: sucesso e popula cache
    user1 = await get_current_user_from_auth_service(token)
    assert isinstance(user1, User)
    assert user1.username == "u"

    # segunda chamada: simula timeout -> deve cair no cache
    user2 = await get_current_user_from_auth_service(token)
    assert user2.username == "u"

    # expira cache e confirma que sem rede falha
    # limpar a entrada do cache explicitamente (mudar TTL não invalida entradas existentes)
    ac._token_cache.pop(token, None)
    monkeypatch.setattr(
        "services.quizz_gen_service.auth_client._TOKEN_CACHE_TTL_SECONDS", 0
    )
    time.sleep(0.01)
    with pytest.raises(HTTPException) as exc:
        await get_current_user_from_auth_service(token)
    assert exc.value.status_code == 503
