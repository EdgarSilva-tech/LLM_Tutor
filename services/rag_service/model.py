# Compatibilidade de import para pytest/CI e runtime em contentores
try:
    from services.rag_service.rag_utils import get_llm, format_question_prompt
except Exception:  # pragma: no cover
    from rag_utils import get_llm, format_question_prompt
from typing import List
from opik.integrations.langchain import OpikTracer

opik_tracer = OpikTracer(project_name="LLM_Tutor")


def question_answer(question: str, context: List[str]) -> str:
    llm = get_llm()
    prompt = format_question_prompt(question, context)
    return llm.invoke(prompt, config={"callbacks": [opik_tracer]})
