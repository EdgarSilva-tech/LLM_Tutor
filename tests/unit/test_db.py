from src import db
from datetime import datetime
from uuid import UUID


def test_khan_academy_lesson_model():
    """Tests the Khan_Academy_Lesson model creation"""
    lesson = db.Khan_Academy_Lesson(
        content_path="data/test_file.txt",
        module="module1",
        topic="topic1",
        date=datetime(2024, 1, 1)
    )
    assert isinstance(lesson.id, UUID)
    assert lesson.content_path == "data/test_file.txt"
    assert lesson.module == "module1"
    assert lesson.topic == "topic1"
    assert lesson.date == datetime(2024, 1, 1)


def test_create_db_and_tables(mocker):
    """Tests the create_db_and_tables function"""
    # Mock the create_all method to avoid creating real tables
    mock_create_all = mocker.patch("sqlmodel.SQLModel.metadata.create_all")
    db.create_db_and_tables()
    mock_create_all.assert_called_once_with(db.engine)


def test_add_classes(mocker):
    """Tests the add_classes function"""
    print("DEBUG: Starting test_add_classes test")

    # Mock external methods and objects
    mock_listdir = mocker.patch("os.listdir", return_value=["test_module1.txt"])
    print(f"DEBUG: Mock listdir configured: {mock_listdir}")

    mock_session = mocker.patch("src.db.Session")
    print(f"DEBUG: Mock Session configured: {mock_session}")

    mock_session_instance = mock_session.return_value.__enter__.return_value
    print(f"DEBUG: Mock session_instance: {mock_session_instance}")

    # Mock uuid for fixed value
    mock_uuid = mocker.patch(
        "uuid.uuid4", return_value=UUID("12345678-1234-5678-1234-567812345678")
    )
    print(f"DEBUG: Mock uuid configured: {mock_uuid}")

    print("DEBUG: Before calling db.add_classes()")
    try:
        db.add_classes()
        print("DEBUG: db.add_classes() executed without exception")
    except Exception as e:
        print(f"DEBUG: Error captured: {e}")
        import traceback
        traceback.print_exc()

    print(f"DEBUG: mock_session_instance.add.call_count = {mock_session_instance.add.call_count}")
    print(f"DEBUG: mock_session_instance.add.call_args_list = {mock_session_instance.add.call_args_list}")

    # Verify that the object was added and committed
    assert mock_session_instance.add.call_count == 1
