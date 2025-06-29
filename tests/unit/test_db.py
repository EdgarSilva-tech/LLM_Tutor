from src import db
from datetime import datetime
from uuid import UUID
import os


def test_khan_academy_lesson_model():
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
    # Mock o método create_all para não criar tabelas reais
    mock_create_all = mocker.patch("sqlmodel.SQLModel.metadata.create_all")
    db.create_db_and_tables()
    mock_create_all.assert_called_once_with(db.engine)


def test_add_classes(mocker):
    print("DEBUG: Iniciando teste test_add_classes")

    # Mock os métodos e objetos externos
    mock_listdir = mocker.patch("os.listdir", return_value=["test_module1.txt"])
    print(f"DEBUG: Mock listdir configurado: {mock_listdir}")

    mock_session = mocker.patch("src.db.Session")
    print(f"DEBUG: Mock Session configurado: {mock_session}")

    mock_session_instance = mock_session.return_value.__enter__.return_value
    print(f"DEBUG: Mock session_instance: {mock_session_instance}")

    # Mock uuid para valor fixo
    mock_uuid = mocker.patch(
        "uuid.uuid4", return_value=UUID("12345678-1234-5678-1234-567812345678")
    )
    print(f"DEBUG: Mock uuid configurado: {mock_uuid}")

    print("DEBUG: Antes de chamar db.add_classes()")
    try:
        db.add_classes()
        print("DEBUG: db.add_classes() executou sem exceção")
    except Exception as e:
        print(f"DEBUG: Erro capturado: {e}")
        import traceback
        traceback.print_exc()

    print(f"DEBUG: mock_session_instance.add.call_count = {mock_session_instance.add.call_count}")
    print(f"DEBUG: mock_session_instance.add.call_args_list = {mock_session_instance.add.call_args_list}")

    # Verifica se o objeto foi adicionado e commitado
    assert mock_session_instance.add.call_count == 1
