from pydantic import BaseModel
from sqlmodel import Field, SQLModel
import uuid
from uuid import UUID
from datetime import datetime
from typing import List


class SingleEvaluationRequest(BaseModel):
    question: str
    answer: str


class EvaluationRequest(BaseModel):
    student_id: str
    quizz_questions: List[str]
    student_answers: List[str]


class Evaluation(SQLModel, table=True):
    eval_id: UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    username: str = Field(index=True)
    question: str
    answer: str
    correct_answer: str
    score: float
    feedback: str
    date: datetime


class User(BaseModel):
    username: str
    email: str | None = None
    full_name: str | None = None
    disabled: bool | None = None


class Token(BaseModel):
    access_token: str
    token_type: str
