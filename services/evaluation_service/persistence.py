from datetime import datetime
from sqlmodel import Session
from logging_config import get_logger
from db import engine
from data_models import Evaluation

logger = get_logger(__name__)


def store_evals(
    username: str,
    question: str,
    answer: str,
    correct_answer: str,
    score: float,
    feedback: str,
):
    with Session(engine) as session:
        try:
            eval = Evaluation(
                username=username,
                question=question,
                answer=answer,
                correct_answer=correct_answer,
                score=score,
                feedback=feedback,
                date=datetime.now(),
            )
            session.add(eval)
            session.commit()
            logger.info(f"Evaluation saved: {eval}")
            return "Evaluation saved"
        except Exception as e:
            logger.exception("Error saving evaluation: %s", e)
            return f"Error saving evaluation: {e}"
