from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from utils.prompts import EVALUATOR_PROMPT, QUIZ_GENERATOR_PROMPT, QUESTION_PROMPT, PLANNER_PROMPT, ROUTER_PROMPT
from typing import List, Literal, Optional
from pydantic import BaseModel, Field
from typing_extensions import Annotated, TypedDict
from graph.state import State
from utils.format_prompt import format_question_prompt, format_quizz_prompt, format_evaluator_prompt, format_router_prompt

    
def get_llm(model_name: str = "gpt-4o-mini", temperature: float = 0.7) -> ChatOpenAI:
    llm = ChatOpenAI(model=model_name, temperature=temperature)
    return llm

def evaluate_answer(question: str, answer: str) -> str:
    llm = get_llm(EVALUATOR_PROMPT)
    prompt = format_evaluator_prompt(question, answer)
    return llm.invoke(prompt)

def generate_quiz(topic: str, num_questions: int, difficulty: str, style: str) -> str:
    llm = get_llm(QUIZ_GENERATOR_PROMPT)
    prompt = format_quizz_prompt(topic, num_questions, difficulty, style)
    return llm.invoke(prompt)

def question_answer(question: str, context: List[str]) -> str:
    llm = get_llm(QUESTION_PROMPT)
    prompt = format_question_prompt(question, context)
    return llm.invoke(prompt)

def route(question: str) -> str:
    llm = get_llm(ROUTER_PROMPT)
    prompt = format_router_prompt(question)
    return llm.invoke(prompt)