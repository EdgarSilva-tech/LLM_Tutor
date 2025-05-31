from graph.state import State
from typing import Literal

def task_selector(state: State) -> Literal["Q&A", "planner"]:
    task = state["task"]

    if task == "Q&A":
        return "Q&A"
    else:
        return "planner"