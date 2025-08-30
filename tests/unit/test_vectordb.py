import pytest
from unittest.mock import Mock, patch, mock_open
from src import vectordb
from src.db import Khan_Academy_Lesson
from uuid import UUID


def test_clean_transcript():
    """Tests the clean_transcript function"""
    # Test with normal text
    text = "Hello world\n- [Instructor] Some text\n- [Voiceover] More text"
    result = vectordb.clean_transcript(text)
    expected = "Hello world Some text More text"
    assert result == expected

    # Test with multiple spaces
    text = "Text   with    multiple     spaces"
    result = vectordb.clean_transcript(text)
    expected = "Text with multiple spaces"
    assert result == expected

    # Test with empty text
    text = ""
    result = vectordb.clean_transcript(text)
    assert result == ""

    # Test with only tags
    text = "- [Instructor]- [Voiceover]"
    result = vectordb.clean_transcript(text)
    assert result == ""


def test_lesson_embeddings_model():
    """Tests the creation of Lesson_Embeddings model"""
    lesson_emb = vectordb.Lesson_Embeddings(
        lesson_id=UUID("12345678-1234-5678-1234-567812345678"),
        chunk_index=0,
        content="Test content",
        embeddings=[0.1, 0.2, 0.3] * 512  # 1536 dimensions
    )

    assert isinstance(lesson_emb.id, UUID)
    assert lesson_emb.lesson_id == UUID("12345678-1234-5678-1234-567812345678")
    assert lesson_emb.chunk_index == 0
    assert lesson_emb.content == "Test content"
    assert len(lesson_emb.embeddings) == 1536


def test_create_db_and_tables(mocker):
    """Tests the create_db_and_tables function"""
    mock_create_all = mocker.patch("sqlmodel.SQLModel.metadata.create_all")

    vectordb.create_db_and_tables()

    mock_create_all.assert_called_once_with(vectordb.engine)


def test_create_embeddings(mocker):
    """Tests the create_embeddings function"""
    # Mock external dependencies
    mock_session = mocker.patch("src.vectordb.Session")
    mock_session_instance = mock_session.return_value.__enter__.return_value

    # Mock select and exec
    mock_select = mocker.patch("src.vectordb.select")
    mock_statement = Mock()
    mock_select.return_value = mock_statement

    # Mock query results
    mock_lesson = Mock(spec=Khan_Academy_Lesson)
    mock_lesson.id = UUID("12345678-1234-5678-1234-567812345678")
    mock_lesson.content_path = "data/test_module1.txt"
    mock_session_instance.exec.return_value = [mock_lesson]

    # Mock open and read
    mock_file_content = "Test lesson content with - [Instructor] and - [Voiceover]"
    mocker.patch("builtins.open", mock_open(read_data=mock_file_content))

    # Mock text_splitter
    mock_doc = Mock()
    mock_doc.page_content = "Test chunk content"
    mock_text_splitter = mocker.patch("src.vectordb.text_splitter")
    mock_text_splitter.create_documents.return_value = [mock_doc]

    # Mock embeddings
    mock_embeddings = mocker.patch("src.vectordb.embeddings")
    mock_embeddings.embed_query.return_value = [0.1] * 1536

    # Mock os.path.exists and os.makedirs
    mocker.patch("os.path.exists", return_value=False)
    mock_makedirs = mocker.patch("os.makedirs")

    # Mock Index
    mock_index = mocker.patch("src.vectordb.Index")
    mock_index_instance = Mock()
    mock_index.return_value = mock_index_instance

    # Execute the function
    vectordb.create_embeddings()

    # Verifications
    mock_session_instance.exec.assert_called()
    mock_text_splitter.create_documents.assert_called_once()
    mock_embeddings.embed_query.assert_called_once_with("Test chunk content")
    mock_session_instance.add.assert_called_once()
    mock_session_instance.commit.assert_called_once()
    mock_session_instance.refresh.assert_called_once()
    mock_makedirs.assert_called_once_with("chunks", exist_ok=True)
    mock_index_instance.create.assert_called_once_with(vectordb.engine)


def test_create_embeddings_with_existing_chunks_dir(mocker):
    """Tests create_embeddings when chunks directory already exists"""
    # Mock external dependencies
    mock_session = mocker.patch("src.vectordb.Session")
    mock_session_instance = mock_session.return_value.__enter__.return_value

    # Mock select and exec
    mock_select = mocker.patch("src.vectordb.select")
    mock_statement = Mock()
    mock_select.return_value = mock_statement

    # Mock query results
    mock_lesson = Mock(spec=Khan_Academy_Lesson)
    mock_lesson.id = UUID("12345678-1234-5678-1234-567812345678")
    mock_lesson.content_path = "data/test_module1.txt"
    mock_session_instance.exec.return_value = [mock_lesson]

    # Mock open and read
    mock_file_content = "Test lesson content"
    mocker.patch("builtins.open", mock_open(read_data=mock_file_content))

    # Mock text_splitter
    mock_doc = Mock()
    mock_doc.page_content = "Test chunk content"
    mock_text_splitter = mocker.patch("src.vectordb.text_splitter")
    mock_text_splitter.create_documents.return_value = [mock_doc]

    # Mock embeddings
    mock_embeddings = mocker.patch("src.vectordb.embeddings")
    mock_embeddings.embed_query.return_value = [0.1] * 1536

    # Mock os.path.exists returning True (directory already exists)
    mocker.patch("os.path.exists", return_value=True)
    mock_makedirs = mocker.patch("os.makedirs")

    # Mock Index
    mock_index = mocker.patch("src.vectordb.Index")
    mock_index_instance = Mock()
    mock_index.return_value = mock_index_instance

    # Execute the function
    vectordb.create_embeddings()

    # Verify that makedirs was not called
    mock_makedirs.assert_not_called()


def test_create_embeddings_multiple_chunks(mocker):
    """Tests create_embeddings with multiple chunks"""
    # Mock external dependencies
    mock_session = mocker.patch("src.vectordb.Session")
    mock_session_instance = mock_session.return_value.__enter__.return_value

    # Mock select and exec
    mock_select = mocker.patch("src.vectordb.select")
    mock_statement = Mock()
    mock_select.return_value = mock_statement

    # Mock query results
    mock_lesson = Mock(spec=Khan_Academy_Lesson)
    mock_lesson.id = UUID("12345678-1234-5678-1234-567812345678")
    mock_lesson.content_path = "data/test_module1.txt"
    mock_session_instance.exec.return_value = [mock_lesson]

    # Mock open and read
    mock_file_content = "Test lesson content"
    mocker.patch("builtins.open", mock_open(read_data=mock_file_content))

    # Mock text_splitter with multiple chunks
    mock_doc1 = Mock()
    mock_doc1.page_content = "Chunk 1 content"
    mock_doc2 = Mock()
    mock_doc2.page_content = "Chunk 2 content"
    mock_text_splitter = mocker.patch("src.vectordb.text_splitter")
    mock_text_splitter.create_documents.return_value = [mock_doc1, mock_doc2]

    # Mock embeddings
    mock_embeddings = mocker.patch("src.vectordb.embeddings")
    mock_embeddings.embed_query.return_value = [0.1] * 1536

    # Mock os.path.exists and os.makedirs
    mocker.patch("os.path.exists", return_value=False)
    mock_makedirs = mocker.patch("os.makedirs")

    # Mock Index
    mock_index = mocker.patch("src.vectordb.Index")
    mock_index_instance = Mock()
    mock_index.return_value = mock_index_instance

    # Execute the function
    vectordb.create_embeddings()

    # Verify that embeddings were created for both chunks
    assert mock_embeddings.embed_query.call_count == 2
    mock_embeddings.embed_query.assert_any_call("Chunk 1 content")
    mock_embeddings.embed_query.assert_any_call("Chunk 2 content")


def test_create_embeddings_no_lessons(mocker):
    """Tests create_embeddings when no lessons are found"""
    # Mock external dependencies
    mock_session = mocker.patch("src.vectordb.Session")
    mock_session_instance = mock_session.return_value.__enter__.return_value

    # Mock select and exec
    mock_select = mocker.patch("src.vectordb.select")
    mock_statement = Mock()
    mock_select.return_value = mock_statement

    # Mock empty query results
    mock_session_instance.exec.return_value = []

    # Execute the function
    vectordb.create_embeddings()

    # Verify that no embeddings were created
    mock_session_instance.add.assert_not_called()
    mock_session_instance.commit.assert_not_called()


def test_create_embeddings_file_not_found(mocker):
    """Tests create_embeddings when lesson file is not found"""
    # Mock external dependencies
    mock_session = mocker.patch("src.vectordb.Session")
    mock_session_instance = mock_session.return_value.__enter__.return_value

    # Mock select and exec
    mock_select = mocker.patch("src.vectordb.select")
    mock_statement = Mock()
    mock_select.return_value = mock_statement

    # Mock query results
    mock_lesson = Mock(spec=Khan_Academy_Lesson)
    mock_lesson.id = UUID("12345678-1234-5678-1234-567812345678")
    mock_lesson.content_path = "data/nonexistent_file.txt"
    mock_session_instance.exec.return_value = [mock_lesson]

    # Mock open to raise FileNotFoundError
    mocker.patch("builtins.open", side_effect=FileNotFoundError("File not found"))

    # Execute the function - should not raise an exception
    try:
        vectordb.create_embeddings()
    except FileNotFoundError:
        pytest.fail("Function should handle FileNotFoundError gracefully")
