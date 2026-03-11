from typing import Any, cast

from sqlmodel import Session
from .db import engine
from .data_models import (
    LearningAssessment,
    MasteryScheduleItemResponse,
    MasteryScheduleResponse,
    MasteryStore,
)
from .logging_config import get_logger
from datetime import datetime
from sqlmodel import select


logger = get_logger(__name__)


def store_learning_assessment(
    username: str,
    quizz_questions: list[str],
    student_answers: list[str],
    scores: list[float],
    feedback: list[dict],
):
    with Session(engine) as session:
        try:
            learning_assessment = LearningAssessment(
                username=username,
                quizz_questions=quizz_questions,
                student_answers=student_answers,
                scores=scores,
                feedback=feedback,
                created_at=datetime.now(),
            )
            session.add(learning_assessment)
            session.commit()
            logger.info(f"Learning assessment saved: {learning_assessment}")
            return "Learning assessment saved"
        except Exception as e:
            logger.exception("Error saving learning assessment: %s", e)
            return f"Error saving learning assessment: {e}"


def get_learning_assessment_by_username(username: str):
    with Session(engine) as session:
        try:
            learning_assessment = session.exec(
                select(LearningAssessment).where(
                    LearningAssessment.username == username
                )
            ).first()
            if learning_assessment is None:
                return None
            return learning_assessment.model_dump()
        except Exception as e:
            logger.exception("Error getting learning assessment by username: %s", e)
            return f"Error getting learning assessment by username: {e}"


def get_learning_assessment_mastery_by_username(username: str):
    with Session(engine) as session:
        try:
            mastery_store = session.exec(
                select(MasteryStore)
                .where(MasteryStore.username == username)
                .order_by(cast(Any, MasteryStore.due_at))
            ).all()
            schedule = [
                MasteryScheduleItemResponse(
                    id=row.id,
                    topic=row.topic,
                    score=row.score,
                    attempts=row.attempts,
                    rolling_avg=row.rolling_avg,
                    last_quiz_id=row.last_quiz_id,
                    updated_at=row.updated_at,
                    mastery_band=row.mastery_band,
                    created_at=row.created_at,
                    status=row.status,
                    action_type=row.action_type,
                    due_at=row.due_at,
                )
                for row in mastery_store
            ]
            return MasteryScheduleResponse(
                username=username,
                schedule=schedule,
            ).model_dump()
        except Exception as e:
            logger.exception("Error getting mastery store by username: %s", e)
            return f"Error getting mastery store by username: {e}"
