from unittest.mock import patch, MagicMock
from services.evaluation_service.eval_utils import format_evaluator_prompt, get_llm
from services.evaluation_service.model import eval_answer
from langchain_core.messages.ai import AIMessage

# --- Test for Prompt Formatting ---


def test_format_evaluator_prompt():
    """
    Tests if the evaluator prompt is formatted correctly
    with the question and answer.
    """
    question = "What is the derivative of x^2?"
    answer = "2x"

    prompt = format_evaluator_prompt(question, answer)

    # Assert that the question and answer are in the formatted prompt
    assert question in prompt
    assert answer in prompt
    # Assert that some key instruction from the base prompt is present
    assert "You are an expert mathematics teacher" in prompt
    assert "Return ONLY this JSON format" in prompt


def test_format_evaluator_prompt_empty_inputs():
    """
    Tests if the function handles empty strings as inputs without errors.
    """
    prompt = format_evaluator_prompt("", "")
    assert "Question: " in prompt
    assert "Student Response: " in prompt


# --- Test for LLM Instantiation ---


@patch("services.evaluation_service.eval_utils.ChatOpenAI")
def test_get_llm(MockChatOpenAI):
    """
    Tests if the get_llm function initializes the ChatOpenAI client
    with the correct model and temperature.
    """
    # Configure the mock to return a specific object
    mock_instance = MockChatOpenAI.return_value

    # Call the function that should instantiate the client
    llm = get_llm(model_name="test-gpt-model", temperature=0.5)

    # Assert if ChatOpenAI class was called once with the expected arguments
    MockChatOpenAI.assert_called_once_with(model="test-gpt-model", temperature=0.5)

    # Assert that the function returned the created instance
    assert llm is mock_instance


# --- Tests for the Main Evaluation Logic ---


@patch("services.evaluation_service.model.format_evaluator_prompt")
@patch("services.evaluation_service.model.get_llm")
def test_eval_answer_success(mock_get_llm, mock_format_prompt):
    """
    Tests the successful execution of the eval_answer function.
    """
    # --- Arrange ---
    # Mock the LLM chain: get_llm -> llm_instance -> invoke
    mock_llm_instance = MagicMock()
    mock_llm_instance.invoke.return_value = AIMessage(content='{"score": 1.0}')
    mock_get_llm.return_value = mock_llm_instance

    # Mock the prompt formatter
    mock_format_prompt.return_value = "This is a formatted prompt"

    question = "What is 2+2?"
    answer = "4"

    # --- Act ---
    result = eval_answer(question, answer)

    # --- Assert ---
    # Check that our mocks were called correctly
    mock_get_llm.assert_called_once()
    mock_format_prompt.assert_called_once_with(question, answer)
    mock_llm_instance.invoke.assert_called_once_with("This is a formatted prompt")

    # Check that the final result is the one from the LLM
    assert result.content == '{"score": 1.0}'


@patch("services.evaluation_service.model.get_llm")
def test_eval_answer_exception_handling(mock_get_llm):
    """
    Tests that the try-except block in eval_answer
    correctly catches and returns exceptions.
    """
    # --- Arrange ---
    # Configure the mocked LLM's invoke method to raise an exception
    mock_llm_instance = MagicMock()
    test_exception = ValueError("LLM API is down")
    mock_llm_instance.invoke.side_effect = test_exception
    mock_get_llm.return_value = mock_llm_instance

    # --- Act ---
    result = eval_answer("any question", "any answer")

    # --- Assert ---
    # Verify that the caught exception is what the function returned
    assert result is test_exception
