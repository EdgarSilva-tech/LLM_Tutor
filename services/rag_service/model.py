# Compatibilidade de import para pytest/CI e runtime em contentores
try:
    from services.rag_service.rag_utils import format_question_prompt, get_llm
except Exception:  # pragma: no cover
    from rag_utils import format_question_prompt, get_llm
from typing import List

from opik.integrations.langchain import OpikTracer
from langchain_core.messages import BaseMessage
from typing import Union


opik_tracer = OpikTracer(
    tags=["langchain", "rag"],
    metadata={"use-case": "question and answer", "version": "1.0"},
    project_name="LLM_Tutor",
)


def question_answer(question: str, context: List[str]) -> Union[str, BaseMessage]:
    llm = get_llm()
    prompt = format_question_prompt(question, context)
    return llm.invoke(prompt, config={"callbacks": [opik_tracer]})
