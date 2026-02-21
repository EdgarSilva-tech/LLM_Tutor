from pydantic import BaseModel
from typing import List
from sqlmodel import Field, SQLModel, Column
import uuid
from uuid import UUID
from datetime import datetime
from sqlalchemy.dialects import postgresql
from sqlalchemy import String, Float


class User(BaseModel):
    username: str
    email: str | None = None
    full_name: str | None = None
    disabled: bool | None = None


class LearningAssessmentRequest(BaseModel):
    quizz_questions: List[str] = Field(sa_column=Column(postgresql.ARRAY(String())))
    student_answers: List[str] = Field(sa_column=Column(postgresql.ARRAY(String())))
    correct_answers: List[str] = Field(sa_column=Column(postgresql.ARRAY(String())))
    scores: List[float] = Field(sa_column=Column(postgresql.ARRAY(Float())))
    feedback: List[dict] = Field(sa_column=Column(postgresql.ARRAY(String())))


class LearningAssessment(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    quizz_id: UUID
    username: str = Field(index=True)
    quizz_questions: List[str] = Field(sa_column=Column(postgresql.ARRAY(String())))
    tags: List[str] = Field(sa_column=Column(postgresql.ARRAY(String())))
    student_answers: List[str] = Field(sa_column=Column(postgresql.ARRAY(String())))
    scores: List[float] = Field(sa_column=Column(postgresql.ARRAY(Float())))
    feedback: List[dict] = Field(sa_column=Column(postgresql.ARRAY(String())))
    created_at: datetime = Field(default_factory=datetime.now)


class MasteryStore(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    username: str = Field(index=True)
    topic: str = Field(index=True)
    score: float
    attempts: int = Field(default=0)
    rolling_avg: float
    last_quiz_id: UUID
    updated_at: datetime = Field(default_factory=datetime.now)
    mastery_band: str
    recency_days: int
    evidence_count: int
    created_at: datetime = Field(default_factory=datetime.now)
    status: str
    action_type: str
    due_at: datetime
