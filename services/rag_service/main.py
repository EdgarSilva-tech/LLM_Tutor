from fastapi import FastAPI, HTTPException
from services.rag_service.model import question_answer
from infra.vectordb import Lesson_Embeddings, postgres_url
from sqlmodel import Session, select, create_engine
from rag_settings import rag_settings
from langchain_openai.embeddings import OpenAIEmbeddings
from services.rag_service.cache import redis_client
from services.rag_service.data_models import (
    QueryRequest, QueryResponse, EmbeddingRequest, EmbeddingResponse
)
import json


app = FastAPI(title="RAG Service")
embeddings = OpenAIEmbeddings(model=rag_settings.model)
engine = create_engine(postgres_url)


@app.post("/rag-service/query")
def query(request: QueryRequest) -> QueryResponse:
    try:
        print(f"request.question: {request.question}")
        question_emb = redis_client.get(request.question)
        print(f"question_emb: {question_emb}")

        if question_emb:
            question_emb = json.loads(question_emb)
            print(f"question_emb: {question_emb}")
        else:
            print("No redis")
            question_emb = embeddings.embed_query(request.question)
            print("Embeddings generated")
            print(f"embeddings: {question_emb}")
            redis_client.set(request.question, json.dumps(question_emb))
            print("Redis set")

        with Session(engine) as session:
            print("Session")
            context = session.exec(
                select(Lesson_Embeddings)
                .order_by(
                    Lesson_Embeddings.embeddings.cosine_distance(question_emb)
                    ).limit(request.top_k)
            )
            print(f"Context: {context}")

            content = [text.content for text in context]
            print(f"Content: {content}")

        response = question_answer(request.question, content)

        return QueryResponse(
                answer=response.content,
                context=content,
                sources=[f"chunk_{i}" for i in range(len(content))]
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"RAG error: {str(e)}")


@app.post("/embed", response_model=EmbeddingResponse)
async def generate_embedding(request: EmbeddingRequest):
    """
    Gera embedding para um texto
    """
    try:
        embedding = redis_client.get(request.text)

        if embedding:
            embedding = json.loads(embedding)
            print(f"embedding: {embedding}")
        else:
            embedding = embeddings.embed_query(request.text)
            print(f"embedding: {embedding}")
            redis_client.set(request.text, json.dumps(embedding))

        return EmbeddingResponse(embedding=embedding)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error while generating embeddings: {str(e)}"
            )


@app.get("/search")
async def search_similar(text: str, top_k: int = 5):
    """
    Busca textos similares
    """
    try:
        text_embedding = redis_client.get(text)

        if text_embedding:
            text_embedding = json.loads(text_embedding)
            print(f"text_embedding: {text_embedding}")
        else:
            text_embedding = embeddings.embed_query(text)
            redis_client.set(text, json.dumps(text_embedding))

        with Session(engine) as session:
            results = session.exec(
                select(Lesson_Embeddings)
                .order_by(Lesson_Embeddings
                          .embeddings
                          .cosine_distance(text_embedding)).limit(top_k)
            )

            return {
                "query": text,
                "results": [
                    {
                        "content": result.content,
                        "chunk_index": result.chunk_index,
                        "lesson_id": str(result.lesson_id)
                    }
                    for result in results
                ]
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")
