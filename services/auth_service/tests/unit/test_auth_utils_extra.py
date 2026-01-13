import pytest
from unittest.mock import patch

from services.auth_service import auth_utils as au
from services.auth_service.data_models import UserInDB


def test_authenticate_user_triggers_rehash_and_updates_password(monkeypatch):
    # user existente com hash atual válido
    plain = "password123"
    current_hash = au.get_password_hash(plain)
    user = UserInDB(
        username="u",
        email="e",
        full_name="U",
        disabled=False,
        hashed_password=current_hash,
    )

    # get_user devolve o utilizador
    monkeypatch.setattr(au, "get_user", lambda username: user)

    # needs_update -> True para forçar rehash
    monkeypatch.setattr(
        au.pwd_context, "needs_update", lambda _hash: True, raising=True
    )

    called = {"n": 0, "new_hash": None}

    def _fake_update(username: str, new_hashed_password: str) -> None:
        called["n"] += 1
        called["new_hash"] = new_hashed_password

    monkeypatch.setattr(au, "_update_user_password", _fake_update, raising=True)

    # act
    result = au.authenticate_user("u", plain)

    # assert: autenticado e update foi chamado
    assert result is not False
    assert result.username == "u"
    assert called["n"] == 1
    assert called["new_hash"] != current_hash
    # o objeto user também deve refletir o novo hash
    assert user.hashed_password == called["new_hash"]


@pytest.mark.asyncio
async def test_get_current_active_user_inactive_raises(monkeypatch):
    # Simula get_current_user a devolver um UserInDB com disabled=True
    inactive = UserInDB(
        username="u",
        email="e",
        full_name="U",
        disabled=True,
        hashed_password="h",
    )

    async def _fake_get_current_user():
        return inactive

    with patch.object(au, "get_current_user", _fake_get_current_user):
        with pytest.raises(Exception) as exc:
            await au.get_current_active_user()
        assert getattr(exc.value, "status_code", None) == 400
