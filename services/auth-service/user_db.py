from sqlmodel import create_engine, Session, SQLModel, Field, select
from .auth_settings import auth_settings
from passlib.context import CryptContext
from uuid import UUID
import uuid


PG_PASSWORD = auth_settings.PG_PASSWORD
DB_NAME = auth_settings.DB_NAME
PORT = auth_settings.PORT

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class User_Auth(SQLModel, table=True):
    user_id: UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    username: str
    email: str | None = None
    full_name: str | None = None
    disabled: bool | None = None
    hashed_password: str


POSTGRES_URL = (
    f"postgresql://postgres:{PG_PASSWORD}@localhost:{PORT}/{DB_NAME}"
    )


engine = create_engine(POSTGRES_URL, echo=True)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def add_user(username: str, email: str, full_name: str, password: str):

    with Session(engine) as session:
        statement = select(User_Auth).where(User_Auth.username == username)
        results = session.exec(statement)

        for row in results:
            if row.username is not None:
                raise Exception("User already exists!")

        new_user = User_Auth(
            username=username,
            email=email,
            full_name=full_name,
            disabled=False,
            hashed_password=pwd_context.hash(password)
        )

        session.add(new_user)
        session.commit()

        session.refresh(new_user)

        print(f"User created: {new_user}")


# if __name__ == "__main__":
#     username = "Edgar_Silva2"
#     email = "edgardasilva10@hotmail.com"
#     full_name = "Edgar Costa Neves da Silva"
#     password = "Test456"

#     create_db_and_tables()
#     add_user(username, email, full_name, password)
