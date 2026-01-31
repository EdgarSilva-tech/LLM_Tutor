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
) -> dict:
    llm = qmod.get_llm()
    prompt = qmod.format_quizz_prompt(topic, num_questions, difficulty, style)
    quizz = ast.literal_eval(llm.invoke(prompt, config={"callbacks": [opik_tracer]}).content)

    if isinstance(quizz, dict):
        if "questions" in quizz and "tags" in quizz:
            if quizz["questions"] is not None and quizz["tags"] is not None:
                return quizz
        else:
            raise ValueError("LLM did not return a parseable list of questions or tags.")
