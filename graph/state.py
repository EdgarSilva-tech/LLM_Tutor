from langgraph.graph import MessagesState
from typing import Literal, Optional


class State(MessagesState):
    task: Literal["Q&A", "Eval", "Quizz"] = None
    topic: str
    summary: str
    num_questions: Optional[int] = None
    difficulty: Optional[Literal["easy", "medium", "hard"]] = None
    style: Optional[Literal["conceptual", "computational", "mixed"]] = None
    quizz_questions: Optional[list[str]] = None
    current_question_index: Optional[int] = None
    correct_answer: Optional[str] = None
    final_answers: Optional[dict[str]] = None
    student_response: Optional[str] = None
    student_responses: list[str]
    explanation: Optional[str] = None
    feedback: Optional[dict[list[dict[str]]]] = None
    user_feedback: Optional[str] = None
