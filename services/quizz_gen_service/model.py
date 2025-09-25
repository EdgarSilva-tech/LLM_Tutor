from quizz_utils import get_llm, format_quizz_prompt


def quizz_generator(topic: str, num_questions: int, difficulty: str, style: str) -> str:
    llm = get_llm()
    prompt = format_quizz_prompt(topic, num_questions, difficulty, style)
    return llm.invoke(prompt)
