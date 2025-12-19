# Compatibilidade de import para pytest/CI e runtime em contentores
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from services.rag_service import rag_utils as rag_mod
else:
    import rag_utils as rag_mod

from opik.integrations.langchain import OpikTracer
from langchain_core.messages import BaseMessage
from typing import Union


opik_tracer = OpikTracer(
    tags=["langchain", "rag"],
    metadata={"use-case": "question and answer", "version": "1.0"},
    project_name="LLM_Tutor",
)


def question_answer(question: str, context: List[str]) -> Union[str, BaseMessage]:
    llm = rag_mod.get_llm()
    prompt = rag_mod.format_question_prompt(question, context)
    result = llm.invoke(prompt, config={"callbacks": [opik_tracer]})
    content = getattr(result, "content", "")
    return str(content)
