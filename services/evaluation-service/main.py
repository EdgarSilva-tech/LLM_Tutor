from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
from graph.nodes import eval
from datetime import datetime
from settings import settings
from sqlmodel import create_engine, Session, SQLModel

app = FastAPI(title="Evaluation Service")
PG_PASSWORD = settings.password
DB_NAME = settings.dbname
PORT = settings.port

postgres_url = (
    f"postgresql://postgres:{PG_PASSWORD}@localhost:{PORT}/{DB_NAME}"
    )

engine = create_engine(postgres_url, echo=True)


class EvaluationRequest(BaseModel):
    student_id: str
    quizz_questions: List[str]
    student_response: str
    correct_answer: str
    feedback: List[str]


class Evaluation(SQLModel, table=True):
    question: str
    answer: str
    feedback: str
    date: datetime


def store_evals(question: str, answer: str, feedback: str):
    engine = create_engine(postgres_url, echo=True)

    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        eval = Evaluation(question=question, answer=answer, feedback=feedback, datetime=datetime.now())
        session.add(eval)
        session.commit()



@app.post("/eval-service")
def evaluation(request: EvaluationRequest):
    if request.quizz_questions:
        request.feedback = []
        question_list = "".join(request.quizz_questions).replace("  ", "").split("\n")
        for question in question_list:
            request.student_response = input(f"{question.strip()}: ")
            request.correct_answer = eval(
                question, request.student_response
            ).content
            # request.student_responses.append(request.student_response)
            store_evals(
                question, request.student_response, request.correct_answer
                )

            request.feedback.append({
                        "question": question,
                        "student_answer": request.student_response,
                        "correct_answer": request.correct_answer,
                    })

        return {"feedback": request.feedback}


@app.post("/eval-service/get_quizz_questions")
def get_quizz_questions(request: EvaluationRequest):
    return {"quizz_questions": request.quizz_questions}


@app.post("/eval-service/evaluate_answer")
def evaluate_answer(question: str):
    student_response = input(f"{question}: ")
    return eval(question, student_response)


@app.get("/eval-service/get-feedback")
def get_feedback(request: EvaluationRequest):
    return {"feedback": request.feedback}