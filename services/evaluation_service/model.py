from eval_utils import get_llm, format_evaluator_prompt


def eval_answer(question: str, answer: str) -> str:
    try:
        llm = get_llm()

        prompt = format_evaluator_prompt(question, answer)
        return llm.invoke(
            prompt,
        )
    except Exception as e:
        return e
