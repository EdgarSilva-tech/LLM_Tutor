from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from services.learning_assement_service import la_utils as la_mod
else:
    from . import la_utils as la_mod
from opik.integrations.langchain import OpikTracer

opik_tracer = OpikTracer(
    tags=["langchain", "quizz"],
    metadata={"use-case": "question generation", "version": "1.0"},
    project_name="LLM_Tutor",
)


def learning_assessment_adviser(
    quizz_questions: list[str],
    student_answers: list[str],
    scores: list[float],
    feedback: list[dict],
):
    llm = la_mod.get_llm()
    evaluation_results: dict = {
        "quizz_questions": [],
        "student_answers": [],
        "scores": [],
        "feedback": [],
    }

    try:
        for q, a, s, f in zip(quizz_questions, student_answers, scores, feedback):
            evaluation_results["quizz_questions"].append(q)
            evaluation_results["student_answers"].append(a)
            evaluation_results["scores"].append(s)
            evaluation_results["feedback"].append(f)

        prompt = la_mod.format_learning_assessment_prompt(evaluation_results)
        response = llm.invoke(prompt, config={"callbacks": [opik_tracer]})
        return response.content

    except Exception as e:
        return f"Error in learning assessment service: {e}"
