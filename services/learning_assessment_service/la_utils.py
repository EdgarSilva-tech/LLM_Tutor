from langchain_openai import ChatOpenAI
from fastapi import HTTPException, status
from .la_settings import la_settings as la_cfg
import opik

OPIK_API_KEY = la_cfg.OPIK_API_KEY
if OPIK_API_KEY:
    opik.configure(api_key=OPIK_API_KEY, workspace="edgarsilva")
else:
    raise ValueError("OPIK_API_KEY is not set")


LEARNING_ASSESSMENT_PROMPT = opik.Prompt(
    name="Learning_Assessment_Prompt",
    prompt="""
You are an expert learning assessor. Analyze the student’s evaluated quiz and decide whether a focused follow‑up quiz is warranted on topics the student struggled with.

Inputs you are given (as a dictionary of lists with the following keys: quizz_questions, student_answers, correct_answers, scores, feedback):

Evaluation results: {evaluation_results}

Decision policy (be consistent and deterministic):
1) Compute accuracy per topic (if a topic is not explicitly given in a question, infer it from the stem conservatively).
1a) Use feedback to refine topic mapping and detect misconceptions. If feedback explicitly flags a misconception, down‑weight that topic’s scores by 0.1 for the decision.
2) A topic is “weak” if:
   - average score for that topic < 0.60, and
   - at least 2 questions were seen for that topic; otherwise treat as insufficient evidence.
3) Overall pass: if no topics are weak and overall average ≥ 0.75 → no focused follow‑up.
4) If any topic is weak, select the single weakest topic (the quiz service currently accepts ONE topic only).
5) Recommend a small follow‑up: num_questions = 5 (default), difficulty = "medium" unless the topic average < 0.40 (then "easy"), style = "mixed".

Output format (STRICT JSON, no prose, no markdown):
{{
  "needs_focus": <true|false>,
  "payloads": [
    {{
      "topic": "<topic-slug-or-clear-name>",
      "num_questions": <int>,
      "difficulty": "<easy|medium|hard>",
      "style": "<computational|conceptual|mixed>"
    }}
  ],

  "rationale": "<one short sentence explaining the decision>"
}}

Rules:
- If needs_focus is false, set payloads to an empty list and still include a short rationale.
- Keep values concise; do not invent topics unrelated to the quiz; prefer exact topic terms present in the questions.
""",
)

REMINDER_PROMPT = opik.Prompt(
    name="Reminder_Prompt",
    prompt="""
    You are a learning assessor. You are given evaluation results and you need to create daily reminders for the student to review the topics
    and example questions and the correct answers to help them improve their mastery.
    Inputs you are given (as a dictionary of lists with the following keys: quizz_questions, student_answers, correct_answers, scores, feedback):
    Evaluation results: {evaluation_results}
    Output format (STRICT JSON, no prose, no markdown):
    {{
        "reminder": "<reminder message>"
    }}

    Rules:
    - The reminder should be a short message that is easy to understand and follow.
    - The reminder should be a daily reminder to review the topics and example questions and the correct answers to help them improve their mastery.
    - The example questions and correct answers should be related to the topics and the feedback given in the evaluation results.
    - The explanation should be in a clear and very detailed step by step format and should be easy to understand and follow.

    Example 1:
    Inputs:
    Evaluation results: {"scores":[0.4,0.0], "feedback":["Missed inner derivative on trig comps"]}

    Output:
    {"reminder":"Today, review the chain rule on trig compositions. Steps: (1) Identify outer and inner functions, (2) Differentiate the outer, keep inner, (3) Multiply by derivative of inner. Worked example: d/dx[sin(x^2+3x)] → outer=sin→cos(·), inner=x^2+3x→2x+3 ⇒ result=cos(x^2+3x)·(2x+3). Practice with d/dx[cos(5x^2−x)] and d/dx[e^(−x^2)]."}

    Example 2:
    Inputs:
    Evaluation results: {"scores":[0.5,0.3], "feedback":["Used chain rule where product rule was needed"]}

    Output:
    {"reminder":"Focus on the product rule: (uv)' = u'v + uv'. Worked example: d/dx[x·e^x] = 1·e^x + x·e^x = e^x(1+x). Contrast with chain rule cases to avoid mixing them. Try d/dx[(2x)·ln x] and d/dx[x^2·sin x]."}

    Example 3:
    Inputs:
    Evaluation results: {"scores":[0.0], "feedback":["Substituted before simplifying removable discontinuity"]}

    Output:
    {"reminder":"Review limits with removable discontinuities. Steps: (1) Factor numerator/denominator, (2) Cancel common factors, (3) Substitute. Worked example: lim_{x→3} [(x^2−9)/(x−3)] → factor (x−3)(x+3)/(x−3) → cancel → lim_{x→3} (x+3)=6. Practice with lim_{x→1}[(x^2−1)/(x−1)]."}
    """,
)


def get_llm(
    model_name: str = "gpt-4o-mini",
    temperature: float = 0.2,
    timeout: float | None = 45.0,
    max_retries: int = 2,
) -> ChatOpenAI:
    api_key = la_cfg.OPENAI_API_KEY
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="OPENAI_API_KEY is not configured in the environment.",
        )
    llm = ChatOpenAI(
        model=model_name,
        temperature=temperature,
        api_key=api_key,
        timeout=timeout,
        max_retries=max_retries,
    )
    return llm


def format_learning_assessment_prompt(evaluation_results: dict) -> str:
    """
    Expects a dict with keys:
      - quizz_questions: list[str]
      - student_answers: list[str]
      - correct_answers: list[str]
      - scores: list[float]
      - feedback: list[dict|str]
    """
    return LEARNING_ASSESSMENT_PROMPT.prompt.format(
        evaluation_results=evaluation_results
    )


def format_reminder_prompt(evaluation_results: dict) -> str:
    """
    Expects a dict with keys:
      - quizz_questions: list[str]
      - student_answers: list[str]
      - correct_answers: list[str]
      - scores: list[float]
      - feedback: list[dict|str]
    """
    return REMINDER_PROMPT.prompt.format(evaluation_results=evaluation_results)
