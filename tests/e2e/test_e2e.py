import os
import time
import asyncio
import pytest
import httpx
from dotenv import load_dotenv

# Carrega especificamente o .env ao lado deste ficheiro (tests/e2e/.env)
load_dotenv()

pytestmark = pytest.mark.e2e


def _get_env_or_skip() -> tuple[str, str, str]:
    base = os.getenv("E2E_BASE_URL")
    user = os.getenv("E2E_USERNAME")
    pwd = os.getenv("E2E_PASSWORD")
    if not base or not user or not pwd:
        pytest.skip("E2E_BASE_URL/E2E_USERNAME/E2E_PASSWORD não definidos")
    return base.rstrip("/"), user, pwd


async def _login_token(
    client: httpx.AsyncClient, base: str, username: str, password: str
) -> str:
    resp = await client.post(
        f"{base}/auth/token",
        data={"username": username, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=15,
    )
    resp.raise_for_status()
    body = resp.json()
    return body["access_token"]


@pytest.mark.asyncio
async def test_e2e_quiz_generate_submit_and_evaluate():
    base, username, password = _get_env_or_skip()
    timeout = httpx.Timeout(60.0, connect=10.0, read=50.0)
    limits = httpx.Limits(keepalive_expiry=5.0)
    transport = httpx.AsyncHTTPTransport(retries=3, limits=limits)
    async with httpx.AsyncClient(timeout=timeout, transport=transport) as client:
        token = await _login_token(client, base, username, password)
        auth = {"Authorization": f"Bearer {token}"}

        # 1) Generate quiz (async)
        gen_payload = {
            "topic": "linear algebra",
            "num_questions": 3,
            "difficulty": "easy",
            "style": "conceptual",
        }
        r = await client.post(
            f"{base}/quiz/generate-async", json=gen_payload, headers=auth
        )
        assert r.status_code in (200, 202)
        quiz_id = r.json().get("quiz_id")
        assert quiz_id
        print(f"[E2E] quiz_id={quiz_id}")

        # 2) Poll job until questions
        deadline = time.time() + 120
        questions = None
        backoff = 0.5
        last_status = None
        last_body = None
        while time.time() < deadline:
            jr = await client.get(f"{base}/quiz/jobs/{quiz_id}", headers=auth)
            last_status = jr.status_code
            try:
                last_body = jr.json()
            except Exception:
                last_body = jr.text
            if jr.status_code == 200:
                data = jr.json()
                qs = data.get("questions")
                if isinstance(qs, list) and qs:
                    questions = qs
                    break
            else:
                # Log auxiliar para entender estados intermediários (ex.: queued/processing/404)
                print(f"[E2E] poll status={last_status} body={last_body}")
            await asyncio.sleep(backoff)
            backoff = min(backoff * 1.7, 5.0)
        assert questions, (
            f"Timeout a obter questões do quiz; last_status={last_status} last_body={last_body}"
        )

        # 3) Submit answers → returns evaluation job_id (use fresh client to avoid stale keep-alive)
        answers = ["answer" for _ in questions]
        await client.aclose()
        limits = httpx.Limits(keepalive_expiry=5.0)
        async with httpx.AsyncClient(
            timeout=timeout,
            transport=httpx.AsyncHTTPTransport(retries=3, limits=limits),
        ) as client2:
            sr = await client2.post(
                f"{base}/quiz/submit-answers",
                json={"quiz_id": quiz_id, "answers": answers},
                headers=auth,
            )
            assert sr.status_code == 202
            job_id = sr.json().get("job_id")
            assert job_id

            # 4) Poll evaluation status (via ingress /evaluation → service /eval-service/jobs/{job_id})
            deadline = time.time() + 60
            status_done = None
            backoff = 0.5
            while time.time() < deadline:
                er = await client2.get(
                    f"{base}/evaluation/eval-service/jobs/{job_id}", headers=auth
                )
                if er.status_code == 200:
                    body = er.json()
                    if body.get("status") == "done":
                        status_done = body
                        break
                await asyncio.sleep(backoff)
                backoff = min(backoff * 1.7, 5.0)
            assert status_done and "feedback" in status_done


@pytest.mark.asyncio
async def test_e2e_rag_question_answer():
    base, username, password = _get_env_or_skip()
    timeout = httpx.Timeout(60.0, connect=10.0, read=50.0)
    limits = httpx.Limits(keepalive_expiry=5.0)
    async with httpx.AsyncClient(
        timeout=timeout, transport=httpx.AsyncHTTPTransport(retries=3, limits=limits)
    ) as client:
        token = await _login_token(client, base, username, password)
        auth = {"Authorization": f"Bearer {token}"}

        payload = {"question": "What is a vector space?", "top_k": 2}
        r = await client.post(f"{base}/rag/question-answer", json=payload, headers=auth)
        assert r.status_code == 200
        data = r.json()
        assert "answer" in data and "context" in data
