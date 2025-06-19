from utils.prompts import QUIZ_GENERATOR_PROMPT, EVALUATOR_PROMPT, QUESTION_PROMPT, ROUTER_PROMPT, PLANNER_PROMPT
from typing import List

def format_quizz_prompt(topic: str, num_questions: int, difficulty: str, style: str) -> str:
    return QUIZ_GENERATOR_PROMPT.prompt.format(topic=topic, num_questions=num_questions, difficulty=difficulty, style=style)

def format_evaluator_prompt(question: str, answer: str) -> str:
    return EVALUATOR_PROMPT.prompt.format(question=question, student_response=answer)

def format_question_prompt(question: str, context: List[float]) -> str:
    return QUESTION_PROMPT.prompt.format(question=question, context=context)

def format_router_prompt(message: str) -> str:
    return ROUTER_PROMPT.prompt.format(message=message)

def format_planner_prompt(task: str, messages: str) -> str:
    return PLANNER_PROMPT.prompt.format(task=task, messages=messages)