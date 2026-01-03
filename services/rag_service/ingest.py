from datetime import datetime
import re
from sqlmodel import Session, select, Index
from db import engine
from langchain_openai.embeddings import OpenAIEmbeddings
from langchain_experimental.text_splitter import SemanticChunker
from rag_settings import rag_settings
from data_models import Khan_Academy_Lesson, Lesson_Embeddings
from pathlib import Path

embeddings = OpenAIEmbeddings(model=rag_settings.model)
text_splitter = SemanticChunker(embeddings)
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"


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
            for lesson in DATA_DIR.iterdir():
                if not lesson.is_file():
                    continue
                name = lesson.name
                # Guardar apenas o nome do ficheiro no caminho persistido
                content_path = f"data/{name}"
                # Extrair módulo de forma robusta
                if "test" in name:
                    after = name.split("test", 1)[1].lstrip("_")
                    module = after[:-4] if after.lower().endswith(".txt") else after
                else:
                    module = Path(name).stem
                topic = "Calculus"
                date = datetime.now()

                class_contents = Khan_Academy_Lesson(
                    content_path=content_path, module=module, topic=topic, date=date
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

        print("Creating embeddings for new lessons...")
        for row in lessons_without_embeddings:
            # Normalizar caminho: usar sempre BASE_DIR/data + nome do ficheiro
            file_name = Path(str(row.content_path).replace("\\", "/")).name
            file_path = (DATA_DIR / file_name).resolve()
            if not file_path.exists():
                raise FileNotFoundError(f"Data file not found: {file_path}")
            with open(file_path, "r", encoding="utf-8") as lesson_file:
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
    add_classes_and_embeddings()
