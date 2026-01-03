from locust import HttpUser, task, between, events
import os
import random
import json
from typing import Any, Dict, List


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
        # 1) gerar quiz async (devolve quiz_id e questions)
        gen_payload = {
            "topic": random.choice(["calculus", "Linear Algebra", "Statistics"]),
            "num_questions": random.choice([3, 4, 5]),
            "difficulty": random.choice(["easy", "medium", "hard"]),
            "style": random.choice(["conceptual", "computational"]),
        }
        resp = self.client.post(
            "/quiz/generate-async",
            json=gen_payload,
        )
        if resp.status_code != 200 and resp.status_code != 202:
            return
        try:
            data = resp.json()
        except Exception:
            return

        quiz_id = data.get("quiz_id")
        questions: List[str] = data.get("questions", [])
        if not quiz_id or not isinstance(questions, list):
            return

        # 2) submeter respostas (mock answers com mesmo comprimento)
        answers = ["answer" for _ in questions]
        submit_payload = {"quiz_id": quiz_id, "answers": answers}
        self.client.post(
            "/quiz/submit-answers",
            json=submit_payload,
        )

    @task(1)
    def auth_users_me(self) -> None:
        self.client.get("/auth/users/me/")
