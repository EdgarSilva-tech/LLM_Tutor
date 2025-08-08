import os
from datetime import datetime
from sqlmodel import create_engine, Session, SQLModel
from services.rag_service.rag_settings import rag_settings
from services.rag_service.data_models import Khan_Academy_Lesson

PG_PASSWORD = rag_settings.PG_PASSWORD
DB_NAME = rag_settings.DB_NAME
PORT = rag_settings.PORT


POSTGRES_URL = (
    f"postgresql://postgres:{PG_PASSWORD}@localhost:{PORT}/{DB_NAME}"
    )

engine = create_engine(POSTGRES_URL, echo=True)


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
                content_path=content_path, module=module,
                topic=topic, date=date
            )

            session.add(class_contents)
            session.commit()

            session.refresh(class_contents)

            print(f"Lesson created: {class_contents}")


if __name__ == "__main__":
    create_db_and_tables()
    add_classes()
