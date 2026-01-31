from sqlmodel import create_engine, SQLModel
from .quizz_settings import quizz_settings

PG_PASSWORD = quizz_settings.PG_PASSWORD
DB_NAME = quizz_settings.DB_NAME
PORT = 5432

POSTGRES_URL = f"postgresql://postgres:{PG_PASSWORD}@postgres:{PORT}/{DB_NAME}"

engine = create_engine(
    POSTGRES_URL,
    echo=True,
    pool_size=10,
    max_overflow=20,
    pool_recycle=1800,
    pool_pre_ping=True,
)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
