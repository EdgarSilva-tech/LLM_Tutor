import pytest
from unittest.mock import patch
from fastapi import HTTPException

# Import the functions to be tested
from services.quizz_gen_service.quizz_utils import format_quizz_prompt, get_llm

# --- Test for Prompt Formatting ---


def test_format_quizz_prompt():
    """
    Tests if the quiz prompt is formatted correctly with all parameters.
    """
    topic = "Derivatives"
    num_questions = 3
    difficulty = "medium"
    style = "computational"

    prompt = format_quizz_prompt(topic, num_questions, difficulty, style)

    # Assert that all input parameters are present in the formatted prompt
    assert topic in prompt
    assert str(num_questions) in prompt
    assert difficulty in prompt
    assert style in prompt
    # Assert that a key instruction from the base prompt is present
    assert "You are a world-class mathematics professor" in prompt


# --- Tests for LLM Instantiation ---


@patch("services.quizz_gen_service.quizz_utils.quizz_cfg")
@patch("services.quizz_gen_service.quizz_utils.ChatOpenAI")
def test_get_llm_success(MockChatOpenAI, mock_quizz_settings):
    """
    Tests if get_llm successfully initializes ChatOpenAI
    when an API key is present.
    """
    # Arrange: Mock the settings to provide an API key
    mock_quizz_settings.OPENAI_API_KEY = "fake-api-key"
    mock_llm_instance = MockChatOpenAI.return_value

    # Act
    llm = get_llm(model_name="test-model", temperature=0.5)

    # Assert
    mock_quizz_settings.configure_mock(OPENAI_API_KEY="fake-api-key")
    MockChatOpenAI.assert_called_once_with(
        model="test-model", temperature=0.5, api_key="fake-api-key"
    )
    assert llm is mock_llm_instance


@patch("services.quizz_gen_service.quizz_utils.quizz_cfg")
def test_get_llm_no_api_key(mock_quizz_settings):
    """
    Tests if get_llm raises an HTTPException when the API key is missing.
    """
    # Arrange: Mock the settings to have no API key
    mock_quizz_settings.OPENAI_API_KEY = None

    # Act & Assert: Check if the correct exception is raised
    with pytest.raises(HTTPException) as excinfo:
        get_llm()

    # Verify the details of the exception
    assert excinfo.value.status_code == 500
    assert "OPENAI_API_KEY is not configured" in excinfo.value.detail
