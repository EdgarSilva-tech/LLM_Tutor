from locust import HttpUser, task, between
import os
import random
import time


def get_env(name: str, default: str = "") -> str:
    val = os.getenv(name)
    return val if val is not None else default


USERNAME = get_env("LOCUST_USERNAME", "Edgar_Silva15")
PASSWORD = get_env("LOCUST_PASSWORD", "test")


class ApiUser(HttpUser):
    wait_time = between(0.5, 2.0)

    def on_start(self) -> None:
        # Autenticação (token)
        form = {
            "username": USERNAME,
            "password": PASSWORD,
        }
        with self.client.post(
            "/auth/token",
            data=form,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            catch_response=True,
        ) as resp:
            if resp.status_code == 200:
                data = resp.json()
                token = data.get("access_token")
                if not token:
                    resp.failure("missing access_token")
                else:
                    self.client.headers.update({"Authorization": f"Bearer {token}"})
            else:
                resp.failure(f"auth failed: {resp.status_code} {resp.text}")

    @task(2)
    def rag_question_answer(self) -> None:
        payload = {
            "question": random.choice(
                [
                    "Explain what a derivative is and how to calculate it briefly.",
                    "What is the Pythagorean theorem?",
                    "Summarize the Goedel's incompleteness theorem.",
                ]
            ),
            "top_k": 3,
        }
        self.client.post(
            "/rag/question-answer",
            json=payload,
        )

    @task(3)
    def quiz_generate_and_submit(self) -> None:
        gen_payload = {
            "topic": random.choice(["calculus", "Linear Algebra", "Statistics"]),
            "num_questions": random.choice([3, 4, 5]),
            "difficulty": random.choice(["easy", "medium", "hard"]),
            "style": random.choice(["conceptual", "computational"]),
        }
        r = self.client.post("/quiz/generate-async", json=gen_payload)
        if r.status_code not in (200, 202):
            return
        data = r.json()
        quiz_id = data.get("quiz_id")
        if not quiz_id:
            return

        # Poll com backoff exponencial até “done” (máx 30s)
        deadline = time.time() + 30
        questions = None
        backoff = 0.5
        while time.time() < deadline:
            jr = self.client.get(f"/quiz/jobs/{quiz_id}")
            if jr.status_code == 200:
                jd = jr.json()
                # quando o consumer acabar, deve devolver questions
                questions = jd.get("questions")
                if isinstance(questions, list) and questions:
                    break
            time.sleep(backoff)
            backoff = min(backoff * 1.7, 5.0)
        if not questions:
            return

        answers = ["answer" for _ in questions]
        self.client.post(
            "/quiz/submit-answers", json={"quiz_id": quiz_id, "answers": answers}
        )

    @task(1)
    def auth_users_me(self) -> None:
        self.client.get("/auth/users/me/")
