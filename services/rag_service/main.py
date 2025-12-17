from fastapi import FastAPI, HTTPException, Depends
from sqlmodel import Session, select
import json
from typing import Annotated, TYPE_CHECKING
from contextlib import asynccontextmanager

if TYPE_CHECKING:
    from services.rag_service.model import question_answer  # type: ignore
    from services.rag_service.cache import redis_client  # type: ignore
    from services.rag_service.data_models import (  # type: ignore
        QueryRequest,
        QueryResponse,
        EmbeddingRequest,
        EmbeddingResponse,
        User,
        Lesson_Embeddings,
    )
    from services.rag_service.auth_client import get_current_active_user  # type: ignore
    from services.rag_service.db import create_db_and_tables, engine  # type: ignore
    from services.rag_service.ingest import add_classes_and_embeddings, embeddings  # type: ignore
    from services.rag_service.logging_config import get_logger  # type: ignore
else:
    from model import question_answer
    from cache import redis_client
    from data_models import (
        QueryRequest,
        QueryResponse,
        EmbeddingRequest,
        EmbeddingResponse,
        User,
        Lesson_Embeddings,
    )
    from auth_client import get_current_active_user
    from db import create_db_and_tables, engine
    from ingest import add_classes_and_embeddings, embeddings
    from logging_config import get_logger

# Initialize the logger for this module
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Creating RAG tables...")
    create_db_and_tables()
    add_classes_and_embeddings()
    logger.info("RAG tables created. Service is ready.")
    yield


app = FastAPI(title="RAG Service", lifespan=lifespan)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "RAG Service"}


@app.post("/question-answer")
def query(
    request: QueryRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> QueryResponse:
    try:
        logger.info(f"request.question: {request.question}")
        question_emb = redis_client.get(request.question)
        logger.info(f"question_emb: {question_emb}")

        if question_emb:
            question_emb = json.loads(question_emb)
            logger.info(f"question_emb: {question_emb}")
        else:
            logger.info("No redis")
            question_emb = embeddings.embed_query(request.question)
            logger.info("Embeddings generated")
            logger.info(f"embeddings: {question_emb}")
            redis_client.set(request.question, json.dumps(question_emb))
            logger.info("Redis set")

        with Session(engine) as session:
            logger.info("Session")
            context = session.exec(
                select(Lesson_Embeddings)
                .order_by(Lesson_Embeddings.embeddings.cosine_distance(question_emb))
                .limit(request.top_k)
            )
            logger.info(f"Context: {context}")

            content = [text.content for text in context]
            logger.info(f"Content: {content}")

        response = question_answer(request.question, content)

        return QueryResponse(
            answer=response,
            context=content,
            sources=[f"chunk_{i}" for i in range(len(content))],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"RAG error: {str(e)}")


@app.post("/embed", response_model=EmbeddingResponse)
async def generate_embedding(
    request: EmbeddingRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    try:
        embedding = redis_client.get(request.text)

        if embedding:
            embedding = json.loads(embedding)
            logger.info(f"embedding found: {embedding}")
        else:
            embedding = embeddings.embed_query(request.text)
            logger.info(f"New embedding generated: {embedding}")
            redis_client.set(
                f"{current_user.username}_{request.text}", json.dumps(embedding)
            )
            logger.info(f"Embedding cached: {embedding}")

        return EmbeddingResponse(embedding=embedding)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error while generating embeddings: {str(e)}"
        )


@app.get("/search")
async def search_similar(
    text: str,
    current_user: Annotated[User, Depends(get_current_active_user)],
    top_k: int = 5,
):
    try:
        text_embedding = redis_client.get(text)

        if text_embedding:
            text_embedding = json.loads(text_embedding)
            logger.info(f"text_embedding: {text_embedding}")
        else:
            text_embedding = embeddings.embed_query(text)
            logger.info(f"New embedding generated: {text_embedding}")
            redis_client.set(
                f"{current_user.username}_{text}", json.dumps(text_embedding)
            )
            logger.info(f"Embedding cached: {text_embedding}")

        with Session(engine) as session:
            results = session.exec(
                select(Lesson_Embeddings)
                .order_by(Lesson_Embeddings.embeddings.cosine_distance(text_embedding))
                .limit(top_k)
            )
            logger.info(f"Search results: {results}")

            return {
                "query": text,
                "results": [
                    {
                        "content": result.content,
                        "chunk_index": result.chunk_index,
                        "lesson_id": str(result.lesson_id),
                    }
                    for result in results
                ],
            }

    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")
