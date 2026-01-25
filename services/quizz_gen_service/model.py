# Compatibilidade de import para pytest/CI e runtime em contentores
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from services.quizz_gen_service import quizz_utils as qmod
else:
    from . import quizz_utils as qmod
from opik.integrations.langchain import OpikTracer
import ast
from typing import Union, List, Any
import json
import re

opik_tracer = OpikTracer(
    tags=["langchain", "quizz"],
    metadata={"use-case": "question generation", "version": "1.0"},
    project_name="LLM_Tutor",
)


def quizz_generator(
    topic: str, num_questions: int, difficulty: str, style: str
) -> List[str]:
    llm = qmod.get_llm()
    prompt = qmod.format_quizz_prompt(topic, num_questions, difficulty, style)
    quizz = llm.invoke(prompt, config={"callbacks": [opik_tracer]})
    val: Union[str, List[Any]] = getattr(quizz, "content", quizz.content)
    # Normalize to list of strings robustly

    if isinstance(val, list):
        items = [str(x).strip() for x in val]
        return items[: max(1, num_questions)]

    if isinstance(val, str):
        text = val.strip()
        # Strip common code fences/markdown
        text = re.sub(r"^```(?:json|python)?\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s*```$", "", text)
        # Try JSON first
        try:
            parsed_json = json.loads(text)
            if isinstance(parsed_json, list):
                items = [str(x).strip() for x in parsed_json]
                return items[: max(1, num_questions)]
        except Exception:
            pass
        # Try Python literal (legacy)
        try:
            parsed = ast.literal_eval(text)
            if isinstance(parsed, list):
                items = [str(x).strip() for x in parsed]
                return items[: max(1, num_questions)]
        except Exception:
            pass
        # Fallback: extract numbered lines like "1. ..." or "- ..."
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        extracted: List[str] = []
        for ln in lines:
            m = re.match(r"^\s*(\d+[\.\)]|-)\s*(.+)$", ln)
            if m:
                extracted.append(m.group(2).strip())
        if extracted:
            return extracted[: max(1, num_questions)]
        raise ValueError("LLM did not return a parseable list of questions.")

    raise TypeError(f"Unexpected LLM result type: {type(val)}")
