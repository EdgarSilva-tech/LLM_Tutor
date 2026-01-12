# Compatibilidade de import para pytest/CI e runtime em contentores
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from services.quizz_gen_service import quizz_utils as qmod
else:
    from . import quizz_utils as qmod
from opik.integrations.langchain import OpikTracer
import ast
from typing import Union, List, Any

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
    print(f"val: {val}")
    print(f"type(val): {type(val)}")

    if isinstance(val, list):
        return [str(x).strip() for x in val]

    if isinstance(val, str):
        parsed = ast.literal_eval(val)
        if not isinstance(parsed, list):
            raise ValueError("LLM did not return a list.")
        return [str(x).strip() for x in parsed]

    raise TypeError(f"Unexpected LLM result type: {type(val)}")


test_quizz = quizz_generator(
    topic="math", num_questions=3, difficulty="medium", style="computational"
)
print(test_quizz)
