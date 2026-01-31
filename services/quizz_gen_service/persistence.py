from sqlmodel import Session
from .db import engine
from .data_models import Quizz
from .logging_config import get_logger
from datetime import datetime

logger = get_logger(__name__)


def store_quizz(
    username: str,
    topic: str,
    num_questions: int,
    difficulty: str,
    style: str,
    questions: list[str],
    tags: list[str],
):
    with Session(engine) as session:
        try:
            quizz = Quizz(
                username=username,
                topic=topic,
                num_questions=num_questions,
                difficulty=difficulty,
                style=style,
                questions=questions,
                tags=tags,
                created_at=datetime.now(),
            )
            session.add(quizz)
            session.commit()
            logger.info(f"Quizz saved: {quizz}")
            return "Quizz saved"
        except Exception as e:
            logger.exception("Error saving quizz: %s", e)
            return f"Error saving quizz: {e}"
