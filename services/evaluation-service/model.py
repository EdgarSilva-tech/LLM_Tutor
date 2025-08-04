from utils.models import get_llm
from utils.format_prompt import format_evaluator_prompt


def eval_answer(question: str, answer: str) -> str:
    llm = get_llm()

    prompt = format_evaluator_prompt(question, answer)
    return llm.invoke(prompt)
