# Compatibilidade de import para pytest/CI e runtime em contentores
try:
    from services.quizz_gen_service.quizz_utils import (  # type: ignore
        format_quizz_prompt,
        get_llm,
    )
except Exception:  # pragma: no cover
    from quizz_utils import format_quizz_prompt, get_llm
from opik.integrations.langchain import OpikTracer

opik_tracer = OpikTracer(
    tags=["langchain", "quizz"],
    metadata={"use-case": "question generation", "version": "1.0"},
    project_name="LLM_Tutor",
)


def quizz_generator(topic: str, num_questions: int, difficulty: str, style: str) -> str:
    llm = get_llm()
    prompt = format_quizz_prompt(topic, num_questions, difficulty, style)
    return llm.invoke(prompt, config={"callbacks": [opik_tracer]})
