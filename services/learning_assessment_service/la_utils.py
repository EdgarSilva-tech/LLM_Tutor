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

Inputs you are given (as a dictionary of lists with the following keys: quizz_questions, student_answers, scores, feedback):

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
      - scores: list[float]
      - feedback: list[dict|str]
    """
    return LEARNING_ASSESSMENT_PROMPT.prompt.format(
        evaluation_results=evaluation_results
    )
