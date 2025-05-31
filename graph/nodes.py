from graph.state import State
from langchain_openai.embeddings import OpenAIEmbeddings
from settings import settings
from src.vectordb import Lesson_Embeddings
from sqlmodel import create_engine, Session, select
from utils.models import question_answer, generate_quiz, planner, evaluate_answer, route

embeddings = OpenAIEmbeddings(model=settings.model)
PG_PASSWORD = settings.password
DB_NAME = settings.dbname
PORT = settings.port

postgres_url = f"postgresql://postgres:{PG_PASSWORD}@localhost:{PORT}/{DB_NAME}"

def answer(state: State):
    question = embeddings.embed_query(state['question'])
    
    engine = create_engine(postgres_url, echo=True)

    with Session(engine) as session:
        context = session.exec(select(Lesson_Embeddings).order_by(Lesson_Embeddings.embeddings.cosine_distance(question)).limit(5))

        content = [text.content for text in context]

    answer = question_answer(state['question'], content)

    return answer.content

def quizz(state: State):

    answer = generate_quiz(state["topic"], state["num_questions"], state["difficulty"], state["style"])

    return answer.content

def router(state: State):
    task = route(state["messages"][-1])
    state["task"] = task
    return task


def plan(state: State):
    return planner(state["messages"])

#def eval(state: State)