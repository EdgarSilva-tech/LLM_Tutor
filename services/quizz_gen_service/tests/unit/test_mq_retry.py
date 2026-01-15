import pytest
from services.quizz_gen_service import mq as mq_mod


@pytest.mark.asyncio
async def test_publish_with_retry_eventual_success(monkeypatch):
    calls = {"n": 0}

    async def _fake_publish(payload, routing_key):
        calls["n"] += 1
        if calls["n"] < 3:
            raise RuntimeError("transient error")
        return None

    # Garante que estado global não interfere
    monkeypatch.setattr(mq_mod, "_publish", _fake_publish, raising=True)
    mq_mod._connection = None
    mq_mod._channel = None

    await mq_mod._publish_with_retry({"a": 1}, "rk", max_retries=3)
    assert calls["n"] == 3
