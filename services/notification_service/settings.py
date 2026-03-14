from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    RABBITMQ_URL: str
    RABBITMQ_EXCHANGE: str = "app.events"
    RABBITMQ_ROUTING_KEY: str = "notification.email.request"
    RABBITMQ_PREFETCH: int = 16
    RABBITMQ_QUEUE_NAME: str = "notification.email.q"
    RABBITMQ_DLX_NAME: str = "app.dlx"
    RABBITMQ_DLQ_NAME: str = "notification.email.dlq"
    RESEND_API_KEY: str


settings = Settings()  # type: ignore[call-arg]
