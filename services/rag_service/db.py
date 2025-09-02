import os
from datetime import datetime
import re
import sqlalchemy as sa
from langchain_experimental.text_splitter import SemanticChunker
from langchain_openai.embeddings import OpenAIEmbeddings
from sqlmodel import create_engine, Session, SQLModel, select, Index
from rag_settings import rag_settings
from data_models import Khan_Academy_Lesson, Lesson_Embeddings

PG_PASSWORD = rag_settings.PG_PASSWORD
DB_NAME = "Khan_Academy"  # Hardcoded for consistency
PORT = 5432  # Hardcoded standard Postgres port
MODEL = rag_settings.model
OPENAI_API_KEY = rag_settings.OPENAI_API_KEY

POSTGRES_URL = (
    f"postgresql://postgres:{PG_PASSWORD}@postgres:{PORT}/{DB_NAME}"
    )

engine = create_engine(POSTGRES_URL, echo=True)
embeddings = OpenAIEmbeddings(model=MODEL, api_key=OPENAI_API_KEY)
text_splitter = SemanticChunker(embeddings)


def create_db_and_tables():
    with Session(engine) as session:
        # Create the vector extension if it doesn't exist
        session.exec(sa.text("CREATE EXTENSION IF NOT EXISTS vector;"))
        session.commit()

    # Now, create all tables
    SQLModel.metadata.create_all(engine)


def clean_transcript(text: str) -> str:
    # text = text.replace('\n', ' ')                         # flatten newlines
    text = text.replace("- [Instructor]", "")
    text = text.replace("- [Voiceover]", "")  # remove tags
    text = re.sub(r"\s+", " ", text).strip()  # collapse whitespace
    return text


def add_classes_and_embeddings():
    with Session(engine) as session:
        # First, add lessons if they don't exist
        if session.exec(select(Khan_Academy_Lesson)).first() is None:
            print("Adding lessons to the database...")
            for lesson in os.listdir("data"):
                content_path = os.path.join("data", lesson)
                module = lesson.split("test")[1].strip("_").strip(".txt")
                topic = "Calculus"
                date = datetime.now()

                class_contents = Khan_Academy_Lesson(
                    content_path=content_path, module=module,
                    topic=topic, date=date
                )
                session.add(class_contents)
            session.commit()
            print("Lessons added.")

        # Now, create embeddings for lessons that don't have them yet
        lessons_without_embeddings = session.exec(
            select(Khan_Academy_Lesson).where(
                ~select(Lesson_Embeddings.lesson_id)
                .where(Lesson_Embeddings.lesson_id == Khan_Academy_Lesson.id)
                .exists()
            )
        ).all()

        if not lessons_without_embeddings:
            print("All lessons already have embeddings. Skipping.")
            return

        print(f"Creating embeddings for {len(lessons_without_embeddings)} new lessons...")
        for row in lessons_without_embeddings:
            filename = row.content_path.split("test_")[-1].replace(".txt", "")
            with open(row.content_path) as lesson_file:
                clean_text = clean_transcript(lesson_file.read())

            chunks = text_splitter.create_documents([clean_text])

            for ii, doc in enumerate(chunks):
                emb_lesson = Lesson_Embeddings(
                    lesson_id=row.id,
                    chunk_index=ii,
                    content=doc.page_content,
                    embeddings=embeddings.embed_query(doc.page_content),
                )
                session.add(emb_lesson)

        session.commit()
        print("Embeddings created successfully.")

        # Create HNSW index for faster similarity search
        index = Index(
            "class_data_index",
            Lesson_Embeddings.embeddings,
            postgresql_using="hnsw",
            postgresql_with={"m": 16, "ef_construction": 64},
            postgresql_ops={"embeddings": "vector_cosine_ops"},
        )
        index.create(bind=engine, checkfirst=True)
        print("HNSW index created or already exists.")


if __name__ == "__main__":
    create_db_and_tables()
    add_classes_and_embeddings()
