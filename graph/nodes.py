import json

from langchain_openai.embeddings import OpenAIEmbeddings
from langgraph.types import interrupt
from sqlmodel import create_engine
from sqlmodel import select
from sqlmodel import Session

from graph.state import State
from settings import settings
from src.vectordb import Lesson_Embeddings
from utils.models import (
    evaluate_answer,
    generate_quizz,
    planner,
    question_answer,
    route,
)

embeddings = OpenAIEmbeddings(model=settings.model)
PG_PASSWORD = settings.password
DB_NAME = settings.dbname
PORT = settings.port

postgres_url = (
    f"postgresql://postgres:{PG_PASSWORD}@localhost:{PORT}/{DB_NAME}"
    )


def answer(state: State):
    question = embeddings.embed_query(state["messages"][-1].content)

    engine = create_engine(postgres_url, echo=True)

    with Session(engine) as session:
        context = session.exec(
            select(Lesson_Embeddings)
            .order_by(Lesson_Embeddings.embeddings.cosine_distance(question))
            .limit(5)
        )

        content = [text.content for text in context]

    answer = question_answer(state["messages"][-1].content, content)

    return {"messages": state["messages"] + [answer.content]}


def quizz(state: State):
    quizz = generate_quizz(
        state["topic"], state["num_questions"],
        state["difficulty"], state["style"]
    )

    return {"quizz_questions": [quizz.content]}


def router(state: State):
    task = route(state["messages"][-1])
    # state["task"] = task.content

    return {"task": task.content}


def plan(state: State):
    if len(state["messages"]) >= 5:
        plan = json.loads(planner(state["task"], state["messages"][-5]).content)
        print(plan)

        return plan
    else:
        plan = json.loads(planner(state["task"], state["messages"]).content)
        print(plan)

        return plan


def eval(state: State):
    feedback = []
    if state["quizz_questions"]:
        question_list = "".join(state["quizz_questions"]).replace("  ", "").split("\n")
        for question in question_list:
            print(f"Current Question: {question.strip()}")
            state["student_response"] = interrupt(f"{question.strip()}: ")
            state["correct_answer"] = evaluate_answer(
                question, state["student_response"]
            ).content
            print(f"State: {state}")
            # state["student_responses"].append(state["student_response"])
            final_feedback = {
                "feedback": feedback.append(
                    {
                        "question": question,
                        "student_answer": state["student_response"],
                        "correct_answer": state["correct_answer"],
                    }
                )
            }
        return final_feedback
