from unittest.mock import patch, MagicMock
from model import question_answer
from rag_utils import format_question_prompt, get_llm
from langchain_core.messages.ai import AIMessage


# Test for format_question_prompt
def test_format_question_prompt():
    question = "What is 2+2?"
    context = ["Basic arithmetic", "Addition"]
    prompt = format_question_prompt(question, context)
    assert question in prompt
    for item in context:
        assert item in prompt
    assert "You are a world-class mathematics tutor" in prompt


# Test for get_llm
@patch('rag_utils.ChatOpenAI')
def test_get_llm(MockChatOpenAI):
    # Configure the mock to behave like the real ChatOpenAI class
    mock_instance = MockChatOpenAI.return_value

    # Call the function to be tested
    llm = get_llm(model_name="test-model", temperature=0.5)

    # Assert that ChatOpenAI was called with the correct parameters
    MockChatOpenAI.assert_called_once_with(model="test-model", temperature=0.5)

    # Assert that the function returned the mock instance
    assert llm == mock_instance


# Test for question_answer
@patch('model.get_llm')
@patch('model.format_question_prompt')
def test_question_answer(mock_format_prompt, mock_get_llm):
    # Arrange
    mock_llm = MagicMock()
    mock_llm.invoke.return_value = AIMessage(content="The answer is 4.")
    mock_get_llm.return_value = mock_llm
    mock_format_prompt.return_value = "Formatted prompt"

    question = "What is 2+2?"
    context = ["Basic arithmetic"]

    # Act
    result = question_answer(question, context)

    # Assert
    mock_get_llm.assert_called_once()
    mock_format_prompt.assert_called_once_with(question, context)
    mock_llm.invoke.assert_called_once_with("Formatted prompt")
    assert result.content == "The answer is 4."


# Test for question_answer with empty context
@patch('model.get_llm')
@patch('model.format_question_prompt')
def test_question_answer_empty_context(mock_format_prompt, mock_get_llm):
    # Arrange
    mock_llm = MagicMock()
    mock_llm.invoke.return_value = AIMessage(content="I need more context.")
    mock_get_llm.return_value = mock_llm
    mock_format_prompt.return_value = "Formatted prompt with no context"

    question = "What is the capital of France?"
    context = []

    # Act
    result = question_answer(question, context)

    # Assert
    mock_get_llm.assert_called_once()
    mock_format_prompt.assert_called_once_with(question, context)
    mock_llm.invoke.assert_called_once_with("Formatted prompt with no context")
    assert result.content == "I need more context."
