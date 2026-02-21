from langchain_core.tools import tool
from .data_models import MasteryStore, LearningAssessment
from sqlmodel import Session
from .db import engine
from .logging_config import get_logger
from .model import learning_assessment_adviser

logger = get_logger(__name__)


@tool
def get_mastery(username: str, topic: str) -> dict:
    try:
        with Session(engine) as session:
            mastery = session.exec(select(MasteryStore).where(MasteryStore.username == username, MasteryStore.topic == topic)).first()
            if not mastery:
                logger.error(f"Mastery not found for user: {username} and topic: {topic}")
                return f"Mastery not found for user: {username} and topic: {topic}"
            return mastery.model_dump()
    except Exception as e:
        logger.error(f"Error getting mastery: {e}")
        return f"Error getting mastery: {e}"


@tool
def list_recent_evaluations(username: str, days: int) -> list[dict]:
    try:
        with Session(engine) as session:
            evaluations = session.exec(select(LearningAssessment).where(LearningAssessment.username == username, LearningAssessment.created_at > datetime.now() - timedelta(days=days))).all()
            return [evaluation.model_dump() for evaluation in evaluations]
    except Exception as e:
        logger.error(f"Error listing recent evaluations: {e}")
        return f"Error listing recent evaluations: {e}"


@tool
def propose_focused_quiz(username: str, quizz_questions: list[str], student_answers: list[str], correct_answers: list[str], scores: list[float], feedback: list[dict]) -> dict:
    try:
        learning_assessment_adviser = learning_assessment_adviser(quizz_questions, student_answers, correct_answers, scores, feedback)
        return learning_assessment_adviser
    except Exception as e:
        logger.error(f"Error proposing focused quiz: {e}")
        return f"Error proposing focused quiz: {e}"
