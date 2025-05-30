from langgraph.graph import MessagesState
from typing import Literal, Optional

class State(MessagesState):
    task: Literal["Q&A", "Eval", "Quizz"]
    topic: str
    num_questions: Optional[int] = None
    difficulty: Optional[Literal["easy", "medium", "hard"]] = None
    style: Optional[Literal["conceptual", "computational", "mixed"]] = None
    quiz_questions: Optional[list[str]] = None
    current_question_index: Optional[int] = None
    question: Optional[str] = None
    correct_answer: Optional[str] = None
    student_response: Optional[str] = None
    explanation: Optional[str] = None
    feedback: Optional[str] = None
    user_feedback: Optional[str] = None
