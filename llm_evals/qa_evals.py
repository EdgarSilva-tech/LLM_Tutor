from opik import Opik
from opik.evaluation.metrics import (
    AnswerRelevance,
    Hallucination,
    Moderation,
    Usefulness,
    ContextPrecision,
    ContextRecall
)
from opik.evaluation import evaluate
from settings import settings
from services.rag_service.model import question_answer
from sqlmodel import Session, select, create_engine
from services.rag_service.data_models import Lesson_Embeddings
from langchain_openai.embeddings import OpenAIEmbeddings

PG_PASSWORD = settings.PG_PASSWORD
DB_NAME = "Khan_Academy"  # Hardcoded for consistency
PORT = 5433  # Hardcoded standard Postgres port
HOST = "127.0.0.1"

POSTGRES_URL = f"postgresql://postgres:{PG_PASSWORD}@{HOST}:{PORT}/{DB_NAME}"
engine = create_engine(POSTGRES_URL, echo=True)
embeddings = OpenAIEmbeddings(model=settings.model)

client = Opik(api_key=settings.OPIK_API_KEY)
metrics = [Hallucination(), AnswerRelevance(), Moderation(),
           Usefulness(), ContextPrecision(), ContextRecall()]
dataset = client.get_or_create_dataset(name="LLM_Tutor_RAG")


def eval_task(x):
    question = embeddings.embed_query(x['question'])

    with Session(engine) as session:
        context = session.exec(
            select(Lesson_Embeddings)
            .order_by(Lesson_Embeddings.embeddings.cosine_distance(question))
            .limit(5)
        )

        content = [text.content for text in context]
    return {
        "output": question_answer(x['question'], content),
        "context": content
    }


evals = evaluate(
    dataset=dataset,
    task=eval_task,
    scoring_metrics=metrics,
    project_name="LLM_Tutor",
    scoring_key_mapping={"input": "question"}
)
