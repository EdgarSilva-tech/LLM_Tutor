from eval_utils import format_evaluator_prompt, get_llm
from opik.integrations.langchain import OpikTracer

opik_tracer = OpikTracer(
    tags=["langchain", "evaluation"],
    metadata={"use-case": "Answer evaluation", "version": "1.0"},
    project_name="LLM_Tutor",
)


def eval_answer(question: str, answer: str) -> str:
    try:
        llm = get_llm()

        prompt = format_evaluator_prompt(question, answer)
        return llm.invoke(prompt, config={"callbacks": [opik_tracer]})
    except Exception as e:
        return e
