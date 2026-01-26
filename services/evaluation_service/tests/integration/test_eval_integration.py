import json
import uuid
import pytest
from fastapi.testclient import TestClient
from sqlmodel import create_engine, Session, select

from services.evaluation_service import main as eval_main
from services.evaluation_service import db as eval_db
from services.evaluation_service import persistence
from services.evaluation_service import model as eval_model
from services.evaluation_service import eval_settings as _settings_mod
from services.evaluation_service.data_models import Evaluation, User


pytest.mark.integration


@pytest.fixture()
def client(tmp_path, monkeypatch):
    # Use a temporary SQLite DB for evaluation service
    db_file = tmp_path / f"eval_{uuid.uuid4().hex}.db"
    engine = create_engine(f"sqlite:///{db_file}?check_same_thread=False", echo=False)
    # Patch engines in both db and persistence
    monkeypatch.setattr(eval_db, "engine", engine, raising=True)
    monkeypatch.setattr(persistence, "engine", engine, raising=True)

    # Patch auth dependency to bypass real auth-service
    async def _fake_current_user():
        return User(
            username="u", email="u@example.com", full_name="User", disabled=False
        )

    monkeypatch.setattr(
        eval_main, "get_current_active_user", _fake_current_user, raising=True
    )

    # Avoid starting real RabbitMQ consumer task during tests
    import asyncio

    def _fake_start_consumer_task():
        t = asyncio.create_task(asyncio.sleep(0))
        t.stop_event = asyncio.Event()
        return t

    monkeypatch.setattr(
        eval_main, "start_consumer_task", _fake_start_consumer_task, raising=True
    )

    # Ensure DB schema exists on our temp engine
    eval_db.create_db_and_tables()

    app = eval_main.app
    with TestClient(app) as c:
        yield c


def test_health_disabled_rabbitmq(client, monkeypatch):
    # Force disable rabbit by clearing URL
    monkeypatch.setattr(_settings_mod.eval_settings, "RABBITMQ_URL", "", raising=True)
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["service"] == "Evaluation Service"
    assert body["rabbitmq"] == "disabled"


def test_evaluation_flow_with_stubbed_llm(client, monkeypatch):
    # Stub LLM to return a fixed evaluation JSON
    class _LLM:
        def invoke(self, prompt, config=None):
            class _Msg:
                content = json.dumps(
                    {
                        "correct_answer": "42",
                        "feedback": "Good attempt, but be precise.",
                        "score": 0.8,
                    }
                )

            return _Msg()

    def _fake_get_llm():
        return _LLM()

    monkeypatch.setattr(eval_model, "get_llm", _fake_get_llm, raising=True)

    # Call /eval-service with two questions
    payload = {
        "student_id": "u",
        "quizz_questions": ["What is 6*7?", "What is 1+1?"],
        "student_answers": ["41", "2"],
    }
    resp = client.post(
        "/eval-service", json=payload, headers={"Authorization": "Bearer t"}
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "request_id" in data
    assert isinstance(data.get("feedback"), list)
    assert len(data["feedback"]) == 2

    # Verify records persisted in DB
    with Session(eval_db.engine) as s:
        rows = list(s.exec(select(Evaluation).where(Evaluation.username == "u")))
        assert len(rows) == 2


def test_get_feedback_and_jobs_endpoints(client, monkeypatch):
    # Preload a feedback entry into DB and Redis via store_evals
    # Then query /eval-service/get-feedback and /eval-service/jobs/{id}
    # Using the same stubbed LLM path as above is not necessary; we directly write via persistence.
    from services.evaluation_service.persistence import store_evals
    from services.evaluation_service.main import redis_client

    # Create a fake feedback and store it, which writes to DB and then set key via /eval-service
    store_res = store_evals(
        username="u",
        question="Q?",
        answer="A",
        correct_answer="C",
        score=1.0,
        feedback="well done",
    )
    assert "Evaluation" in store_res

    # Simulate a job result in Redis
    job_id = "job-abc"
    redis_client.set(job_id, json.dumps([{"question": "Q?", "score": 1.0}]), ex=3600)

    # get-feedback (DB-backed values are returned via mget of keys; we mimic that by storing a key)
    gf = client.get("/eval-service/get-feedback", headers={"Authorization": "Bearer t"})
    assert gf.status_code == 200

    # jobs endpoint: will return processing if not found, or done if key exists under Eval:u:job_id.
    # Seed expected key name and verify done.
    redis_client.set(
        f"Eval:u:{job_id}", json.dumps([{"q": "Q", "score": 1.0}]), ex=3600
    )
    jr = client.get(
        f"/eval-service/jobs/{job_id}", headers={"Authorization": "Bearer t"}
    )
    assert jr.status_code == 200
    assert jr.json().get("status") == "done"


def test_feedback_not_visible_to_other_user(monkeypatch):
    # Seed feedback for user 'u'
    from services.evaluation_service.main import redis_client, app as eval_app

    redis_client.set("Eval:u:req-1", json.dumps([{"q": "Q", "score": 1.0}]), ex=3600)

    # Switch auth to another user 'v' and check /get-feedback
    async def _fake_user_v():
        return User(username="v", email="v@example.com", full_name="V", disabled=False)

    eval_app.dependency_overrides[eval_main.get_current_active_user] = _fake_user_v
    with TestClient(eval_app) as c2:
        r = c2.get("/eval-service/get-feedback", headers={"Authorization": "Bearer t"})
        assert r.status_code == 200
        # No Eval:v:* keys exist, endpoint returns informative string
        assert r.json() == "No keys found for the pattern."
