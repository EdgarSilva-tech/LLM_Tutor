from pydantic_settings import BaseSettings, SettingsConfigDict


class Auth_Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    PG_PASSWORD: str
    DB_NAME: str = "Users"
    PORT: int = 5432


auth_settings = Auth_Settings()
