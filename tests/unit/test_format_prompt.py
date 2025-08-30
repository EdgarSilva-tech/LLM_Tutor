import pytest
from unittest.mock import patch, Mock
from utils import format_prompt


class TestFormatQuizzPrompt:
    """Testes para a função format_quizz_prompt"""
    
    def test_format_quizz_prompt_basic(self, mocker):
        """Testa formatação básica do prompt de quiz"""
        # Mock do template de prompt
        mock_prompt = Mock()
        mock_prompt.prompt = "Generate {num_questions} questions about {topic} with {difficulty} difficulty in {style} style"
        mocker.patch("utils.format_prompt.QUIZ_GENERATOR_PROMPT", mock_prompt)
        
        result = format_prompt.format_quizz_prompt(
            topic="Calculus",
            num_questions=5,
            difficulty="medium",
            style="multiple choice"
        )
        
        expected = "Generate 5 questions about Calculus with medium difficulty in multiple choice style"
        assert result == expected
    
    def test_format_quizz_prompt_with_special_characters(self, mocker):
        """Testa formatação com caracteres especiais no tópico"""
        mock_prompt = Mock()
        mock_prompt.prompt = "Topic: {topic}, Questions: {num_questions}"
        mocker.patch("utils.format_prompt.QUIZ_GENERATOR_PROMPT", mock_prompt)
        
        result = format_prompt.format_quizz_prompt(
            topic="Calculus & Algebra",
            num_questions=3,
            difficulty="hard",
            style="essay"
        )
        
        expected = "Topic: Calculus & Algebra, Questions: 3"
        assert result == expected


class TestFormatEvaluatorPrompt:
    """Testes para a função format_evaluator_prompt"""
    
    def test_format_evaluator_prompt_basic(self, mocker):
        """Testa formatação básica do prompt de avaliação"""
        mock_prompt = Mock()
        mock_prompt.prompt = "Question: {question}\nStudent Answer: {student_response}"
        mocker.patch("utils.format_prompt.EVALUATOR_PROMPT", mock_prompt)
        
        result = format_prompt.format_evaluator_prompt(
            question="What is the derivative of x²?",
            answer="2x"
        )
        
        expected = "Question: What is the derivative of x²?\nStudent Answer: 2x"
        assert result == expected
    
    def test_format_evaluator_prompt_with_long_text(self, mocker):
        """Testa formatação com texto longo"""
        mock_prompt = Mock()
        mock_prompt.prompt = "Q: {question}\nA: {student_response}"
        mocker.patch("utils.format_prompt.EVALUATOR_PROMPT", mock_prompt)
        
        long_question = "Explain in detail the fundamental theorem of calculus and its applications"
        long_answer = "The fundamental theorem of calculus connects differentiation and integration..."
        
        result = format_prompt.format_evaluator_prompt(long_question, long_answer)
        
        expected = f"Q: {long_question}\nA: {long_answer}"
        assert result == expected


class TestFormatQuestionPrompt:
    """Testes para a função format_question_prompt"""
    
    def test_format_question_prompt_basic(self, mocker):
        """Testa formatação básica do prompt de pergunta"""
        mock_prompt = Mock()
        mock_prompt.prompt = "Question: {question}\nContext: {context}"
        mocker.patch("utils.format_prompt.QUESTION_PROMPT", mock_prompt)
        
        context = [0.1, 0.2, 0.3, 0.4, 0.5]
        result = format_prompt.format_question_prompt(
            question="What is the limit?",
            context=context
        )
        
        expected = "Question: What is the limit?\nContext: [0.1, 0.2, 0.3, 0.4, 0.5]"
        assert result == expected
    
    def test_format_question_prompt_empty_context(self, mocker):
        """Testa formatação com contexto vazio"""
        mock_prompt = Mock()
        mock_prompt.prompt = "Q: {question}, C: {context}"
        mocker.patch("utils.format_prompt.QUESTION_PROMPT", mock_prompt)
        
        result = format_prompt.format_question_prompt(
            question="Simple question",
            context=[]
        )
        
        expected = "Q: Simple question, C: []"
        assert result == expected
    
    def test_format_question_prompt_large_context(self, mocker):
        """Testa formatação com contexto grande"""
        mock_prompt = Mock()
        mock_prompt.prompt = "Context: {context}\nQuestion: {question}"
        mocker.patch("utils.format_prompt.QUESTION_PROMPT", mock_prompt)
        
        large_context = [0.1] * 100  # 100 elementos
        result = format_prompt.format_question_prompt(
            question="Test question",
            context=large_context
        )
        
        expected = f"Context: {large_context}\nQuestion: Test question"
        assert result == expected


class TestFormatRouterPrompt:
    """Testes para a função format_router_prompt"""
    
    def test_format_router_prompt_basic(self, mocker):
        """Testa formatação básica do prompt de roteamento"""
        mock_prompt = Mock()
        mock_prompt.prompt = "Message: {message}"
        mocker.patch("utils.format_prompt.ROUTER_PROMPT", mock_prompt)
        
        result = format_prompt.format_router_prompt("Hello, I need help")
        
        expected = "Message: Hello, I need help"
        assert result == expected
    
    def test_format_router_prompt_empty_message(self, mocker):
        """Testa formatação com mensagem vazia"""
        mock_prompt = Mock()
        mock_prompt.prompt = "Input: {message}"
        mocker.patch("utils.format_prompt.ROUTER_PROMPT", mock_prompt)
        
        result = format_prompt.format_router_prompt("")
        
        expected = "Input: "
        assert result == expected


class TestFormatPlannerPrompt:
    """Testes para a função format_planner_prompt"""
    
    def test_format_planner_prompt_basic(self, mocker):
        """Testa formatação básica do prompt de planejamento"""
        mock_prompt = Mock()
        mock_prompt.prompt = "Task: {task}\nMessages: {messages}"
        mocker.patch("utils.format_prompt.PLANNER_PROMPT", mock_prompt)
        
        result = format_prompt.format_planner_prompt(
            task="Create a study plan",
            messages="Previous conversation history"
        )
        
        expected = "Task: Create a study plan\nMessages: Previous conversation history"
        assert result == expected
    
    def test_format_planner_prompt_complex_task(self, mocker):
        """Testa formatação com tarefa complexa"""
        mock_prompt = Mock()
        mock_prompt.prompt = "Objective: {task}\nContext: {messages}"
        mocker.patch("utils.format_prompt.PLANNER_PROMPT", mock_prompt)
        
        complex_task = "Design a comprehensive learning path for calculus including prerequisites, core concepts, and advanced topics"
        messages = "Student background: High school graduate, interested in engineering"
        
        result = format_prompt.format_planner_prompt(complex_task, messages)
        
        expected = f"Objective: {complex_task}\nContext: {messages}"
        assert result == expected


class TestIntegration:
    """Testes de integração para verificar se todas as funções funcionam juntas"""
    
    def test_all_format_functions_with_real_templates(self):
        """Testa todas as funções de formatação com templates reais"""
        # Este teste verifica se as funções não quebram com templates reais
        # (sem mockar os templates)
        
        # Teste format_quizz_prompt
        quiz_result = format_prompt.format_quizz_prompt(
            topic="Mathematics",
            num_questions=3,
            difficulty="easy",
            style="true/false"
        )
        assert isinstance(quiz_result, str)
        assert len(quiz_result) > 0
        
        # Teste format_evaluator_prompt
        eval_result = format_prompt.format_evaluator_prompt(
            question="Test question?",
            answer="Test answer"
        )
        assert isinstance(eval_result, str)
        assert len(eval_result) > 0
        
        # Teste format_question_prompt
        question_result = format_prompt.format_question_prompt(
            question="Test question",
            context=[0.1, 0.2]
        )
        assert isinstance(question_result, str)
        assert len(question_result) > 0
        
        # Teste format_router_prompt
        router_result = format_prompt.format_router_prompt("Test message")
        assert isinstance(router_result, str)
        assert len(router_result) > 0
        
        # Teste format_planner_prompt
        planner_result = format_prompt.format_planner_prompt(
            task="Test task",
            messages="Test messages"
        )
        assert isinstance(planner_result, str)
        assert len(planner_result) > 0
