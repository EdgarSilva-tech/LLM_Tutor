from sqlmodel import create_engine, Session, select
from auth_settings import auth_settings
from passlib.context import CryptContext
from passlib.hash import bcrypt_sha256
from data_models import User_Auth, auth_metadata


PG_PASSWORD = auth_settings.PG_PASSWORD
DB_NAME = auth_settings.DB_NAME
PORT = 5432

pwd_context = CryptContext(schemes=["bcrypt_sha256", "bcrypt"], deprecated="auto")

POSTGRES_URL = f"postgresql://postgres:{PG_PASSWORD}@postgres:{PORT}/{DB_NAME}"


engine = create_engine(POSTGRES_URL, echo=True)


def create_db_and_tables():
    auth_metadata.create_all(engine)


def add_user(username: str, email: str, full_name: str, password: str):
    with Session(engine) as session:
        statement = select(User_Auth).where(User_Auth.username == username)
        results = session.exec(statement)
        print(f"Results: {results}")

        for row in results:
            if row.username is not None:
                raise Exception("User already exists!")

        new_user = User_Auth(
            username=username,
            email=email,
            full_name=full_name,
            disabled=False,
            # Força uso explícito de bcrypt_sha256,
            # evitando limites de 72 bytes
            hashed_password=bcrypt_sha256.hash(password),
        )
        print(f"New user: {new_user}")

        session.add(new_user)
        session.commit()

        session.refresh(new_user)

        print(f"User created: {new_user}")

        return new_user


def update_user_password(username: str, new_hashed_password: str) -> None:
    """Atualiza o hash da password para migração transparente."""
    with Session(engine) as session:
        statement = select(User_Auth).where(User_Auth.username == username)
        user = session.exec(statement).first()
        if user is None:
            return
        user.hashed_password = new_hashed_password
        session.add(user)
        session.commit()


# if __name__ == "__main__":
#     username = "Edgar_Silva12"
#     email = "edgardasilva10@hotmail.com"
#     full_name = "Edgar Costa Neves da Silva"
#     password = "Test456"

#     # create_db_and_tables()
#     add_user(username, email, full_name, password)
