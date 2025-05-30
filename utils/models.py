from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from utils.prompts import EVALUATOR_PROMPT, QUIZ_GENERATOR_PROMPT, QUESTION_PROMPT, PLANNER_PROMPT
from typing import List, Literal, Optional
from pydantic import BaseModel, Field
from typing_extensions import Annotated, TypedDict
from graph.state import State
from utils.format_prompt import format_question_prompt

class next_task(BaseModel):
    task: Literal["Q&A", "Eval", "Quizz"] = Field(description="The setup of the joke")

    
def get_llm(prompt: str, model_name: str = "gpt-4o-mini", temperature: float = 0.7) -> ChatOpenAI:
    prompt_template = ChatPromptTemplate.from_template(prompt)
    llm = ChatOpenAI(model=model_name, temperature=temperature)
    return llm

def evaluate_answer(question: str, answer: str) -> str:
    evaluator = get_llm(EVALUATOR_PROMPT)
    return evaluator.invoke({"question": question, "answer": answer})

def generate_quiz(topic: str, num_questions: int, difficulty: str, style: str) -> str:
    quiz_generator = get_llm(QUIZ_GENERATOR_PROMPT)
    return quiz_generator.invoke({"topic": topic, "num_questions": num_questions, "dificulty": difficulty, "style": style})

def question_answer(question: str, context: List[str]) -> str:
    answer = get_llm(QUESTION_PROMPT)
    prompt = format_question_prompt(question, context)
    return answer.invoke(prompt)

def planner(question: str) -> str:
    plan = get_llm(PLANNER_PROMPT).with_structured_output(next_task)
    return plan.invoke(question)