from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file="./services/rag_service/.env",
                                      extra="ignore")

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
    REDIS_PORT: int = 13255
    REDIS_DB: int = 0
    REDIS_USERNAME: str = "default"
    REDIS_ENDPOINT: str
    REDIS_PASSWORD: str
    AUTH_SECRET: str
    ALGORITHM: str = "HS256"


rag_settings = Settings()
