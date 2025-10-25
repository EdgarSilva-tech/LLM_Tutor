# Compatibilidade de import para pytest/CI e runtime em contentores
try:
    from services.quizz_gen_service.quizz_utils import get_llm, format_quizz_prompt  # type: ignore
except Exception:  # pragma: no cover
    from quizz_utils import get_llm, format_quizz_prompt


def quizz_generator(topic: str, num_questions: int, difficulty: str, style: str) -> str:
    llm = get_llm()
    prompt = format_quizz_prompt(topic, num_questions, difficulty, style)
    return llm.invoke(prompt)
