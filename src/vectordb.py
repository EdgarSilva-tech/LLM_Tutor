from pgvector.sqlalchemy import Vector
from sqlmodel import Session, SQLModel, Field, create_engine, Index, select
from typing import Any
import os
from dotenv import load_dotenv
import re
from langchain_experimental.text_splitter import SemanticChunker
from langchain_openai.embeddings import OpenAIEmbeddings
from uuid import UUID
import uuid
import sqlalchemy as sa
from db import Khan_Academy_Lesson

load_dotenv()
PG_PASSWORD = os.getenv("password")

embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

text_splitter = SemanticChunker(embeddings)

def clean_transcript(text: str) -> str:
    #text = text.replace('\n', ' ')                         # flatten newlines
    text = text.replace('- [Instructor]', '')
    text = text.replace('- [Voiceover]', '')             # remove tags
    text = re.sub(r'\s+', ' ', text).strip()               # collapse whitespace
    return text

class Lesson_Embeddings(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    lesson_id: UUID = Field(foreign_key="khan_academy_lesson.id")
    chunk_index: int
    content: str
    embeddings: Any = Field(sa_type=Vector(1536))

db_name = "Khan_Academy"
postgres_url = f"postgresql://postgres:{PG_PASSWORD}@localhost:5432/{db_name}"

engine = create_engine(postgres_url, echo=True)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def create_embeddings():
    with Session(engine) as session:
        ext = 'CREATE EXTENSION IF NOT EXISTS vector;'
        session.exec(sa.text(ext))

        statement = select(Khan_Academy_Lesson)
        results = session.exec(statement)

        for row in results:
            filename = row.content_path.split("test_")[-1].replace(".txt", "")
            print(f"filename: {filename}")
            with open(row.content_path, "r") as lesson_file:
                clean_text = clean_transcript(lesson_file.read())
                print(f"text: {clean_text}")

            chunks = text_splitter.create_documents([clean_text])
            
            #chunks = text_splitter.split_text(text)
            if not os.path.exists("chunks"):
                os.makedirs("chunks", exist_ok=True)

            for ii, doc in enumerate(chunks):
                print(f"Page content: {doc.page_content}")
                with open(os.path.join("chunks", f"{filename}_chunk_{ii}.txt"), "w") as file:
                    text = file.write(doc.page_content)
                    print(f"File text: {text}")

                    emb_lesson = Lesson_Embeddings(lesson_id=row.id, chunk_index=ii, content=doc.page_content, embeddings=embeddings.embed_query(doc.page_content))

                    session.add(emb_lesson)
                    session.commit()

                    session.refresh(emb_lesson)

                    print(f"Embeddings created: {emb_lesson}")

        index = Index(
            'class_data_index',
            Lesson_Embeddings.embeddings,
            postgresql_using='hnsw',
            postgresql_with={'m': 16, 'ef_construction': 64},
            postgresql_ops={'embeddings': 'vector_cosine_ops'}
        )
        index.create(engine)


if __name__ == "__main__":
    create_db_and_tables()
    create_embeddings()