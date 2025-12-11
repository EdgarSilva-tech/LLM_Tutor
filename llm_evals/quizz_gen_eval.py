from opik import Opik
from opik.evaluation.metrics import (
    GEval,
    Hallucination,
    AnswerRelevance
)
from opik.evaluation import evaluate
from settings import settings
from services.quizz_gen_service.model import quizz_generator

client = Opik(api_key=settings.OPIK_API_KEY)
metrics = [Hallucination(), AnswerRelevance(require_context=False), GEval(
    task_introduction="""You are a world-class mathematics professor
    tasked with generating a math quizz.
    """,
    evaluation_criteria="""
    The quizz should be appropriate for high school (AP) or
    college-level math, the difficulty should match the level specified,
    the style should match: e.g., 'conceptual' = explanations or reasoning,
    'computational' = step-by-step problems, it must return only the questions
    — no answers, no explanations,
    format clearly using numbered python list (e.g., 1., 2., 3., ...),
    include only the questions and don't insert unneccessary text such as
    ### Generated Quiz:
    """
),
           ]
dataset = client.get_or_create_dataset(name="LLM_Tutor_QuizzGen")


def eval_task(x):
    difficulty = x['difficulty']
    style = x['style']
    topic = x['topic']
    num_questions = x['num_questions']

    output = quizz_generator(topic, num_questions, difficulty, style)
    return {
        "output": output,
    }


evals = evaluate(
    dataset=dataset,
    task=eval_task,
    scoring_metrics=metrics,
    # prompt=[QUESTION_PROMPT],
    project_name="LLM_Tutor",
    scoring_key_mapping={"input": "learning_objective"}
)

# scores = evals.aggregate_evaluation_scores()
# for metric_name, statistics in scores.aggregated_scores.items():
#     print(f"{metric_name}: {statistics}")
