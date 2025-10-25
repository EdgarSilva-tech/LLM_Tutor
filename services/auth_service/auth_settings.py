from pydantic_settings import BaseSettings, SettingsConfigDict


class AuthSettings(BaseSettings):
    # Database settings
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    PG_PASSWORD: str | None = None
    DB_NAME: str | None = None
    DB_PORT: int = 5432

    # JWT settings
    SECRET_KEY: str | None = None
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ALGORITHM: str = "HS256"


auth_settings = AuthSettings()
