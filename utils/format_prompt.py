from utils.prompts import QUIZ_GENERATOR_PROMPT, EVALUATOR_PROMPT, QUESTION_PROMPT
from typing import List

def format_quizz_prompt(topic: str, num_questions: int, difficulty: str, style: str) -> str:
    return QUIZ_GENERATOR_PROMPT.format(topic=topic, num_questions=num_questions, difficulty=difficulty, style=style)

def format_evaluator_prompt(question: str, answer: str) -> str:
    return EVALUATOR_PROMPT.format(question=question, answer=answer)

def format_question_prompt(question: str, context: List[float]) -> str:
    return QUESTION_PROMPT.format(question=question, context=context)
