from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    OPENAI_API_KEY: str
    OPIK_API_KEY: str
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 10279
    REDIS_DB: int = 0
    REDIS_USERNAME: str = "default"
    REDIS_ENDPOINT: str
    REDIS_PASSWORD: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    RABBITMQ_URL: str
    DB_NAME: str
    DB_PORT: int
    PG_PASSWORD: str
    USERNAME: str
    HOST: str

    RABBITMQ_USER: str
    RABBITMQ_PASS: str
    RABBITMQ_EXCHANGE: str = "app.events"
    RABBITMQ_ROUTING_KEY: str = "quiz.generate.request"
    RABBITMQ_PREFETCH: int = 16


la_settings = Settings()
