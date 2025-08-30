from pydantic_settings import BaseSettings, SettingsConfigDict


class AuthSettings(BaseSettings):
    # Database settings
    model_config = SettingsConfigDict(env_file=".env",
                                      extra="ignore")
    PG_PASSWORD: str
    DB_NAME: str
    DB_PORT: int

    # JWT settings
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ALGORITHM: str


auth_settings = AuthSettings()
