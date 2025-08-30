from utils import models


def test_evaluate_answer(mocker):
    mock_llm = mocker.Mock()
    mocker.patch(
        "utils.models.get_llm", return_value=mock_llm
        )
    mocker.patch(
        "utils.models.format_evaluator_prompt", return_value="eval prompt"
        )
    mock_llm.invoke.return_value = "eval result"

    result = models.evaluate_answer("Q", "A")

    models.format_evaluator_prompt.assert_called_once_with("Q", "A")
    mock_llm.invoke.assert_called_once_with("eval prompt")
    assert result == "eval result"


def test_generate_quiz(mocker):
    mock_llm = mocker.Mock()
    mocker.patch(
        "utils.models.get_llm", return_value=mock_llm
        )
    mocker.patch(
        "utils.models.format_quizz_prompt", return_value="quiz prompt"
        )
    mock_llm.invoke.return_value = "quiz result"

    result = models.generate_quizz("math", 5, "easy", "multiple-choice")

    models.format_quizz_prompt.assert_called_once_with(
        "math", 5, "easy", "multiple-choice"
    )
    mock_llm.invoke.assert_called_once_with("quiz prompt")
    assert result == "quiz result"


def test_question_answer(mocker):
    mock_llm = mocker.Mock()
    mocker.patch(
        "utils.models.get_llm", return_value=mock_llm
        )
    mocker.patch(
        "utils.models.format_question_prompt", return_value="qa prompt"
        )
    mock_llm.invoke.return_value = "answer"

    result = models.question_answer("What is AI?", ["context1", "context2"])

    models.format_question_prompt.assert_called_once_with(
        "What is AI?", ["context1", "context2"]
    )
    mock_llm.invoke.assert_called_once_with("qa prompt")
    assert result == "answer"


def test_route(mocker):
    mock_llm = mocker.Mock()
    mocker.patch(
        "utils.models.get_llm", return_value=mock_llm
        )
    mocker.patch(
        "utils.models.format_router_prompt", return_value="route prompt"
        )
    mock_llm.invoke.return_value = "route result"

    result = models.route("What should I do?")

    models.format_router_prompt.assert_called_once_with("What should I do?")
    mock_llm.invoke.assert_called_once_with("route prompt")
    assert result == "route result"


def test_planner(mocker):
    mock_llm = mocker.Mock()
    mocker.patch(
        "utils.models.get_llm", return_value=mock_llm
        )
    mocker.patch(
        "utils.models.format_planner_prompt", return_value="planner prompt"
        )
    mock_llm.invoke.return_value = "plan result"

    result = models.planner("task", "messages")

    models.format_planner_prompt.assert_called_once_with("task", "messages")
    mock_llm.invoke.assert_called_once_with("planner prompt")
    assert result == "plan result"
