import os
import uuid
from datetime import datetime
from uuid import UUID
from sqlmodel import create_engine, Field, Session, SQLModel
from settings import settings

PG_PASSWORD = settings.PG_PASSWORD
DB_NAME = settings.dbname
PORT = settings.port


class Khan_Academy_Lesson(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    content_path: str
    module: str
    topic: str
    date: datetime


postgres_url = f"postgresql://postgres:{PG_PASSWORD}@localhost:{PORT}/{DB_NAME}"

engine = create_engine(postgres_url, echo=True)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def add_classes():
    with Session(engine) as session:
        for lesson in os.listdir("data"):
            content_path = os.path.join("data", lesson)
            module = lesson.split("test")[1].strip("_").strip(".txt")
            topic = "Calculus"
            date = datetime.now()

            class_contents = Khan_Academy_Lesson(
                content_path=content_path, module=module, topic=topic, date=date
            )

            session.add(class_contents)
            session.commit()

            session.refresh(class_contents)

            print(f"Lesson created: {class_contents}")


if __name__ == "__main__":
    create_db_and_tables()
    add_classes()
