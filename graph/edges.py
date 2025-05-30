from graph.state import State
from typing import Literal

def task_selector(state: State) -> Literal["Q&A", "Eval", "Quizz"]:
    task = state["task"]

    if task == "generate_quiz":
        return "Quizz"
    elif task == "Evaluate":
        return "Eval"
    else:
        return "Q&A"
