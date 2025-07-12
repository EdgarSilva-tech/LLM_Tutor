from fastapi import FastAPI, HTTPException
from typing import List
from model import question_answer
from infra.vectordb import Lesson_Embeddings, postgres_url
from sqlmodel import Session, select, create_engine
from settings import settings
from langchain_openai.embeddings import OpenAIEmbeddings
from pydantic import BaseModel
from infra.redis_cache import redis_client


class QueryRequest(BaseModel):
    question: str
    top_k: int = 5


class QueryResponse(BaseModel):
    answer: str
    context: List[str]
    sources: List[str]


class EmbeddingRequest(BaseModel):
    text: str


class EmbeddingResponse(BaseModel):
    embedding: List[float]


app = FastAPI(title="RAG Service")
embeddings = OpenAIEmbeddings(model=settings.model)
engine = create_engine(postgres_url)


@app.post("/rag-service/query")
def query(request: QueryRequest) -> str:
    try:
        question_emb = redis_client.get(request.question)

        if question_emb is None:
            question_emb = embeddings.embed_query(request.question)
            redis_client.set(request.question, question_emb)

        with Session(engine) as session:
            context = session.exec(
                select(Lesson_Embeddings)
                .order_by(
                    Lesson_Embeddings.embeddings.cosine_distance(question_emb)
                    ).limit(request.top_k)
            )

            content = [text.content for text in context]

        response = question_answer(request.question, content)

        return QueryResponse(
                answer=response.content,
                context=content,
                sources=[f"chunk_{i}" for i in range(len(content))]
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro no RAG: {str(e)}")
    

@app.post("/embed", response_model=EmbeddingResponse)
async def generate_embedding(request: EmbeddingRequest):
    """
    Gera embedding para um texto
    """
    try:
        embedding = redis_client.get(request.text)

        if embedding is None:
            embedding = embeddings.embed_query(request.text)
            redis_client.set(request.text, embedding)

        return EmbeddingResponse(embedding=embedding)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar embedding: {str(e)}")


@app.get("/search")
async def search_similar(text: str, top_k: int = 5):
    """
    Busca textos similares
    """
    try:
        text_embedding = redis_client.get(text)

        if text_embedding is None:
            text_embedding = embeddings.embed_query(text)
            redis_client.set(text, text_embedding)

        with Session(engine) as session:
            results = session.exec(
                select(Lesson_Embeddings)
                .order_by(Lesson_Embeddings.embeddings.cosine_distance(text_embedding))
                .limit(top_k)
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
        raise HTTPException(status_code=500, detail=f"Erro na busca: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
