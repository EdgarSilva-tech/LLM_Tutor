import opik
from langchain_openai import ChatOpenAI

from typing import TYPE_CHECKING

# Compat imports para pytest/CI e execuçāo em contentores
if TYPE_CHECKING:
    from services.quizz_gen_service.quizz_settings import quizz_settings as quizz_cfg
else:
    try:
        from services.quizz_gen_service.quizz_settings import (
            quizz_settings as quizz_cfg,
        )
    except Exception:  # pragma: no cover
        from quizz_settings import quizz_settings as quizz_cfg
from fastapi import HTTPException, status


OPIK_API_KEY = quizz_cfg.OPIK_API_KEY
if OPIK_API_KEY:
    opik.configure(api_key=OPIK_API_KEY, workspace="edgarsilva")
else:
    raise ValueError("OPIK_API_KEY is not set")

QUIZZ_GENERATOR_PROMPT = opik.Prompt(
    name="Quizz_Generator_Promt",
    prompt="""
You are a world-class mathematics professor tasked with generating a math quizz.

The goal is to help students review and practice a specific topic.

Generate a quizz based on the following inputs:
- **Topic**: {topic}
- **Number of questions**: {num_questions}
- **Difficulty**: {difficulty} (easy | medium | hard)
- **Style**: {style} (computational | conceptual | mixed)

Guidelines:
- Questions should be appropriate for high school (AP) or college-level math
- The difficulty should match the level specified
- The style should match: e.g., "conceptual" = explanations or reasoning, "computational" = step-by-step problems
- You must return only the questions — no answers, no explanations
- Format clearly using numbered python list (e.g., 1., 2., 3., ...)
- Include only the questions and don't insert unneccessary text such as ### Generated Quiz:
- Return only the questions in a Python list format and a list of tags, no other text or explanations, no markdown formatting

---

### 📘 Example 1

**Topic**: Chain Rule
**Number of Questions**: 3
**Difficulty**: medium
**Style**: computational

**Generated Quiz**:

{{"questions": ["1. Differentiate the function f(x) = (3x² + 5x)⁴",
"2. If f(x) = e^(x²), what is f '(x)?",
"3. Find the derivative of y = sin(2x³ + 1)"],
"tags": ["calculus", "derivatives", "chain rule"]
}}

---

### 📘 Example 2

**Topic**: Applications of Derivatives
**Number of Questions**: 2
**Difficulty**: hard
**Style**: conceptual


{{"questions": ["1. Explain how the second derivative of a function relates to the concavity of its graph and provide an example",
"2. A function has a local maximum at x = 2. What conditions must be true about its first and second derivatives at that point"],
"tags": ["calculus", "derivatives", "chain rule"]
}}

---

Now generate the quiz:
- Topic: {topic}
- Number of questions: {num_questions}
- Difficulty: {difficulty}
- Style: {style}
""",
)


def get_llm(
    model_name: str = "gpt-4o-mini",
    temperature: float = 0.2,
    timeout: float | None = 45.0,
    max_retries: int = 2,
) -> ChatOpenAI:
    api_key = quizz_cfg.OPENAI_API_KEY
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


def format_quizz_prompt(
    topic: str, num_questions: int, difficulty: str, style: str
) -> str:
    return QUIZZ_GENERATOR_PROMPT.prompt.format(
        topic=topic, num_questions=num_questions, difficulty=difficulty, style=style
    )
