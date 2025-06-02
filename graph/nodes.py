from graph.state import State
from langchain_openai.embeddings import OpenAIEmbeddings
from settings import settings
from src.vectordb import Lesson_Embeddings
from sqlmodel import create_engine, Session, select
from utils.models import question_answer, generate_quiz, planner, evaluate_answer, route
from langgraph.types import interrupt

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

    return {"messages": state["messages"] + [answer.content]}

def quizz(state: State):

    answer = generate_quiz(state["topic"], state["num_questions"], state["difficulty"], state["style"])

    return {"quizz_questions": answer.content}

def router(state: State):
    task = route(state["messages"][-1])
    state["task"] = task
    return {"task": task.content}


def plan(state: State):
    if len(state["messages"]) >= 5:
        return planner(state["task"], state["messages"][-5]).content
    else:
        return planner(state["task"], state["messages"]).content
    
def eval(state: State):
    feedback = []
    if state["quizz_questions"]:
        for question in state["quizz_questions"]:
            state["student_response"] = interrupt({"query": question})["data"]
            state["correct_answer"] = evaluate_answer(question, state["student_response"]).content
            state["student_responses"].append(state["student_response"])
            feedback.append({"question": question, "student_answer": state["student_response"], "correct_answer": state["correct_answer"]})
        return feedback
    else:
        state["student_response"] = interrupt({"query": question})["data"]
        state["correct_answer"] = evaluate_answer(state["question"], state["student_response"]).content
        feedback.append({"question": question, "student_answer": state["student_response"], "correct_answer": state["correct_answer"]})
        return feedback