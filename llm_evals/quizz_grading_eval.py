from opik import Opik
from opik.evaluation.metrics import GEval, Hallucination, AnswerRelevance
from opik.evaluation import evaluate
from settings import settings
from services.evaluation_service.model import eval_answer

client = Opik(api_key=settings.OPIK_API_KEY)
metrics = [
    Hallucination(),
    AnswerRelevance(require_context=False),
    GEval(
        task_introduction="""You are a world-class mathematics professor acting as an impartial grader-of-graders.
    You will evaluate the quality of an assistant that graded a student's answer.
    You are given: (1) the question, (2) a reference_solution, (3) the student_answer,
    and (4) the evaluator_output (which includes a the evaluator correct answer, numeric score in [0,1] and feedback text).
    Your job is to judge whether the evaluator_output is accurate, fair, and useful.
    """,
        evaluation_criteria="""Judge the evaluator_output against the following criteria:
    1) Score correctness & calibration:
    - The numeric score must reflect the student_answer correctness vs reference_solution.
    - Accept equivalent reasoning and alternate correct solutions.
    - Mapping guideline (not strict but indicative):
        correct/complete ≈ 0.9–1.0
        mostly correct (small gaps) ≈ 0.7–0.85
        partially correct (major gaps) ≈ 0.4–0.65
        mostly incorrect ≈ 0.1–0.35
        incorrect/off-topic ≈ 0.0–0.05
    - Penalize severe misgrading (e.g., giving high score to incorrect answers).

    2) Feedback usefulness:
    - Specific and actionable; points out misconceptions and missing steps.
    - References key elements from the reference_solution where relevant.
    - Concise, clear, and oriented a helping the student improve.

    3) Faithfulness & non-hallucination:
    - No invented facts unrelated to the question.
    - Do not introduce content that contradicts the reference_solution.

    4) Coverage & alignment:
    - Mentions the most important aspects required by the question.
    - Mention what is missing and, when appropriate, suggest the correct path.

    5) Tone & safety:
    - Professional, neutral, and respectful.

    Your final judgment should consider all aspects above. Favour evaluator_outputs
    that are calibrated, fair, and provide concrete, actionable feedback.
    """,
    ),
]
dataset = client.get_or_create_dataset(name="LLM_Tutor_Grading")


def eval_task(x):
    question = x["question"]
    student_answer = x["student_answer"]

    output = eval_answer(question, student_answer)

    return {
        "output": output,
    }


evals = evaluate(
    dataset=dataset,
    task=eval_task,
    scoring_metrics=metrics,
    # prompt=[QUESTION_PROMPT],
    project_name="LLM_Tutor",
    scoring_key_mapping={"input": "question"},
)