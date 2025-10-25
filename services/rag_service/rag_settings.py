from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DB_NAME: str
    USERNAME: str
    PG_PASSWORD: str
    HOST: str
    PORT: int = 5432
    OPENAI_API_KEY: str
    model: str = "text-embedding-3-small"
    messages_after_summary: int = 5
    summary_trigger: int = 20
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 12258
    REDIS_DB: int = 0
    REDIS_USERNAME: str = "default"
    REDIS_ENDPOINT: str
    REDIS_PASSWORD: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    OPIK_API_KEY: str


rag_settings = Settings()
