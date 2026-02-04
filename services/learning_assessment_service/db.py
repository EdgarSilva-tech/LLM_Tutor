from sqlmodel import create_engine, SQLModel
from .la_settings import la_settings

PG_PASSWORD = la_settings.PG_PASSWORD
DB_NAME = la_settings.DB_NAME
PORT = la_settings.DB_PORT

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
