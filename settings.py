from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    dbname: str = "LLM_Tutor"
    username: str
    password: str
    host: str
    port: int = 5432
    OPENAI_API_KEY: str
    model: str = "text-embedding-3-small"

settings = Settings()