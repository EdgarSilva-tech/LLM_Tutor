from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 11683
    REDIS_DB: int = 0
    REDIS_USERNAME: str = "default"
    REDIS_ENDPOINT: str
    REDIS_PASSWORD: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    OPENAI_API_KEY: str
    OPIK_API_KEY: str

    # RabbitMQ
    RABBITMQ_URL: str
    RABBITMQ_EXCHANGE: str = "app.events"
    RABBITMQ_ROUTING_KEY: str = "quiz.generate.request"
    RABBITMQ_PREFETCH: int = 16


quizz_settings = Settings()
