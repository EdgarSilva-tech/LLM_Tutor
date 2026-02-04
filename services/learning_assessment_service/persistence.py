from sqlmodel import Session
from .db import engine
from .data_models import LearningAssessment
from .logging_config import get_logger
from datetime import datetime

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
