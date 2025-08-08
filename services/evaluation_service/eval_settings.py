from pydantic_settings import BaseSettings, SettingsConfigDict


class EvalSettings(BaseSettings):
    # Database settings
    model_config = SettingsConfigDict(
        env_file="./services/evaluation_service/.env", extra="ignore"
        )
    PG_PASSWORD: str
    DB_NAME: str
    DB_PORT: int
    OPENAI_API_KEY: str
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 13255
    REDIS_DB: int = 0
    REDIS_USERNAME: str = "default"
    REDIS_ENDPOINT: str
    REDIS_PASSWORD: str


eval_settings = EvalSettings()
