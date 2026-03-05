from langchain_core.tools import tool
from .data_models import MasteryStore, LearningAssessment
from sqlmodel import Session, select
from datetime import datetime, timedelta
from .db import engine
from .logging_config import get_logger
from fastapi import HTTPException

logger = get_logger(__name__)


@tool
def get_mastery(username: str, topic: str) -> dict:
    try:
        with Session(engine) as session:
            mastery = session.exec(
                select(MasteryStore).where(
                    MasteryStore.username == username, MasteryStore.topic == topic
                )
            ).first()
            if not mastery:
                logger.error(
                    f"Mastery not found for user: {username} and topic: {topic}"
                )
                raise HTTPException(status_code=404, detail=f"Mastery not found for user: {username} and topic: {topic}")
            return mastery.model_dump()
    except Exception as e:
        logger.error(f"Error getting mastery: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting mastery: {e}")


@tool
def list_recent_evaluations(username: str, days: int) -> list[dict]:
    try:
        with Session(engine) as session:
            evaluations = session.exec(
                select(LearningAssessment).where(
                    LearningAssessment.username == username,
                    LearningAssessment.created_at
                    > datetime.now() - timedelta(days=days),
                )
            ).all()
            return [evaluation.model_dump() for evaluation in evaluations]
    except Exception as e:
        logger.error(f"Error listing recent evaluations: {e}")
        raise HTTPException(status_code=500, detail=f"Error listing recent evaluations: {e}")