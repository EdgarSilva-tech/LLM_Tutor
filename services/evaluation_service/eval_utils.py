import opik
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from services.evaluation_service.eval_settings import eval_settings as eval_cfg
else:
    try:
        from services.evaluation_service.eval_settings import eval_settings as eval_cfg
    except Exception:
        from eval_settings import eval_settings as eval_cfg

load_dotenv()
OPIK_API_KEY = eval_cfg.OPIK_API_KEY
if OPIK_API_KEY:
    opik.configure(
        api_key=OPIK_API_KEY,
    )
else:
    raise ValueError("OPIK_API_KEY is not set")


EVALUATOR_PROMPT = opik.Prompt(
    name="Evaluator_Prompt",
    prompt="""
You are an expert mathematics teacher. Your task is to evaluate a student's answer to a math question.

IMPORTANT: You must respond with ONLY a valid JSON object. No additional text, explanations, or formatting.

Your job is to:
1. Determine if the student's answer is fully correct, partially correct, or incorrect
2. Explain your reasoning clearly and concisely
3. Give constructive feedback — what they got right, what they missed, and how to improve
4. Assign a score from 0 to 1

Return ONLY this JSON format (no newlines, no extra spaces):
{{"correct_answer": "Your answer here", "feedback": "Your feedback here", "score": 0.8}}

Rules:
- Score must be between 0.0 and 1.0
- 1.0 = fully correct
- 0.7-0.9 = mostly correct with minor issues
- 0.4-0.6 = partially correct
- 0.1-0.3 = some understanding but major errors
- 0.0 = completely incorrect
---

### 📘 Example 1

**Question**: What is the derivative of f(x) = sin(x²)?
**Correct Answer**: f '(x) = 2x * cos(x²)
**Student Answer**: f '(x) = cos(x²)

**Evaluation**:
The student has the right idea by using the chain rule but forgot to multiply by the derivative of the inner function x². The correct answer includes the extra factor of 2x.

✅ Feedback: You're close! You applied the chain rule, but missed one part. Remember that when differentiating sin(x²), you also need to multiply by the derivative of x², which is 2x. So the full answer is 2x * cos(x²).

💯 Score: 0.5

---

### 📘 Example 2

**Question**: Find the area of a circle with radius 3
**Correct Answer**: 9π
**Student Answer**: 9π

**Evaluation**:
The student answered correctly and showed understanding of the area formula A = πr².

✅ Feedback: Perfect! You correctly used the formula A = πr² with r = 3 to get 9π.

💯 Score: 1.0

---

### 📘 Example 3

**Question**: Explain how the derivative of a function relates to its graph
**Correct Answer**: The derivative represents the slope of the function. A positive derivative means the function is increasing, negative means decreasing, and zero means horizontal (possible extrema).
**Student Answer**: It shows if it’s going up or down.

**Evaluation**:
The student's answer is mostly correct, but too vague. They understand the idea that the derivative indicates direction, but didn’t explain slope or mention key cases.

✅ Feedback: Good intuition! You're right that the derivative tells you whether a graph is increasing or decreasing. Next time, try to include terms like “slope,” and mention what happens when the derivative is zero (horizontal tangent line or extrema).

💯 Score: 0.7

---

Now evaluate the student's answer below using the same format:
- Question: {question}
- Student Response: {student_response}

Please give your answer to the question and compare it witn the when evaluating and explain the reason behind the grade
""",
)


def get_llm(model_name: str = "gpt-4o-mini", temperature: float = 0.7) -> ChatOpenAI:
    llm = ChatOpenAI(model=model_name, temperature=temperature)
    return llm


def format_evaluator_prompt(question: str, answer: str) -> str:
    return EVALUATOR_PROMPT.prompt.format(question=question, student_response=answer)
