import sqlalchemy as sa
from langchain_openai.embeddings import OpenAIEmbeddings
from sqlmodel import create_engine, Session, SQLModel
from rag_settings import rag_settings
from langchain_experimental.text_splitter import SemanticChunker

PG_PASSWORD = rag_settings.PG_PASSWORD
DB_NAME = "Khan_Academy"  # Hardcoded for consistency
PORT = 5432  # Hardcoded standard Postgres port
MODEL = rag_settings.model
OPENAI_API_KEY = rag_settings.OPENAI_API_KEY

POSTGRES_URL = f"postgresql://postgres:{PG_PASSWORD}@postgres:{PORT}/{DB_NAME}"

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


# if __name__ == "__main__":
#     create_db_and_tables()
