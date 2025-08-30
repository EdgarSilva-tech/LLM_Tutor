import json

from langchain_openai.embeddings import OpenAIEmbeddings
from langgraph.types import interrupt
from sqlmodel import create_engine
from sqlmodel import select
from sqlmodel import Session

from graph.state import State
from settings import settings
from src.vectordb import Lesson_Embeddings
from langchain_core.messages import HumanMessage, RemoveMessage
from utils.models import (
    evaluate_answer,
    generate_quizz,
    planner,
    question_answer,
    route,
    get_llm
)
from functools import lru_cache


embeddings = OpenAIEmbeddings(model=settings.model)
PG_PASSWORD = settings.PG_PASSWORD
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
        print(f"Plan: {plan}")

        return plan
    else:
        plan = json.loads(planner(state["task"], state["messages"]).content)
        print(f"Plan: {plan}")

        return plan


@lru_cache(maxsize=128)
def eval(state: State):
    if state["quizz_questions"]:
        state["feedback"] = []
        question_list = "".join(state["quizz_questions"]).replace("  ", "").split("\n")
        for question in question_list:
            state["student_response"] = interrupt(f"{question.strip()}: ")
            state["correct_answer"] = evaluate_answer(
                question, state["student_response"]
            ).content
            print(f"State: {state}")
            # state["student_responses"].append(state["student_response"])
            state["feedback"].append({
                        "question": question,
                        "student_answer": state["student_response"],
                        "correct_answer": state["correct_answer"],
                    })

        return {"feedback": state["feedback"]}


def summarize_conversation(state: State):
    model = get_llm()
    summary = state.get("summary", "")

    if summary:
        summary_message = (
            f"This is summary of the conversation to date between LLM Tutor and the user: {summary}\n\n"
            "Extend the summary by taking into account the new messages above:"
        )
    else:
        summary_message = (
            "Create a summary of the conversation above between LLM Tutor and the user. "
            "The summary must be a short description of the conversation so far, "
            "but that captures all the relevant information shared between LLM Tutor and the user "
            "such as topics of evaluations, questions asked, student responses and feedback"
        )

    messages = state["messages"] + [HumanMessage(content=summary_message)]
    response = model.invoke(messages)

    delete_messages = [RemoveMessage(id=m.id) for m in state["messages"][: -settings.messages_after_summary]]
    return {"summary": response.content, "messages": delete_messages}
