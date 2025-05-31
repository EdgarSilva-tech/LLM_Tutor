from langchain_openai import ChatOpenAI
from utils.format_prompt import format_question_prompt, format_quizz_prompt, format_evaluator_prompt, format_router_prompt, format_planner_prompt
from typing import List
    
def get_llm(model_name: str = "gpt-4o-mini", temperature: float = 0.7) -> ChatOpenAI:
    llm = ChatOpenAI(model=model_name, temperature=temperature)
    return llm

def evaluate_answer(question: str, answer: str) -> str:
    llm = get_llm()
    prompt = format_evaluator_prompt(question, answer)
    return llm.invoke(prompt)

def generate_quiz(topic: str, num_questions: int, difficulty: str, style: str) -> str:
    llm = get_llm()
    prompt = format_quizz_prompt(topic, num_questions, difficulty, style)
    return llm.invoke(prompt)

def question_answer(question: str, context: List[str]) -> str:
    llm = get_llm()
    prompt = format_question_prompt(question, context)
    return llm.invoke(prompt)

def route(question: str) -> str:
    llm = get_llm()
    prompt = format_router_prompt(question)
    return llm.invoke(prompt)

def planner(task: str, message: str) -> str:
    llm = get_llm()
    prompt = format_planner_prompt(task, message)
    return llm.invoke(prompt)