from utils.format_prompt import format_question_prompt
from utils.models import get_llm
from typing import List


def question_answer(question: str, context: List[str]) -> str:
    llm = get_llm()
    prompt = format_question_prompt(question, context)
    return llm.invoke(prompt)
