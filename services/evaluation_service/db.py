from sqlmodel import create_engine, SQLModel
from eval_settings import eval_settings

PG_PASSWORD = eval_settings.PG_PASSWORD
DB_NAME = eval_settings.DB_NAME
PORT = 5432  # Hardcoded standard Postgres port

POSTGRES_URL = (
    f"postgresql://postgres:{PG_PASSWORD}@postgres:{PORT}/{DB_NAME}"
    )

engine = create_engine(POSTGRES_URL, echo=True)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
