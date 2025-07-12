from graph.state import State
from typing import Literal
from langgraph.graph import END
from settings import settings


def task_selector(state: State) -> Literal["Q&A", "planner"]:

    if state["task"] == "Q&A":
        return "Q&A"
    else:
        return "planner"


def to_summarize_or_to_not_summarize(state: State) -> Literal["summarize", "__end__"]:
    messages = state["messages"]

    if len(messages) >= settings.summary_trigger:
        return "summarize"

    return END
