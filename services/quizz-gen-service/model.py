from utils.models import get_llm
from utils.prompts import format_quizz_prompt


def generate_quizz(topic: str, num_questions: int, difficulty: str, style: str) -> str:
    llm = get_llm()
    prompt = format_quizz_prompt(topic, num_questions, difficulty, style)
    return llm.invoke(prompt)
