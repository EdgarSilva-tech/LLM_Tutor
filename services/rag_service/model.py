from rag_utils import get_llm, format_question_prompt
from typing import List


def question_answer(question: str, context: List[str]) -> str:
    llm = get_llm()
    prompt = format_question_prompt(question, context)
    return llm.invoke(prompt)
