from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 12498
    REDIS_DB: int = 0
    REDIS_USERNAME: str = "default"
    REDIS_ENDPOINT: str
    REDIS_PASSWORD: str
    AUTH_SECRET: str
    ALGORITHM: str = "HS256"
    OPENAI_API_KEY: str


quizz_settings = Settings()
