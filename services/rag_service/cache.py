# utils/redis_config.py
import redis
from rag_settings import rag_settings


class RedisConfig:
    def __init__(self):
        self.host = rag_settings.REDIS_ENDPOINT
        self.username = rag_settings.REDIS_USERNAME
        self.password = rag_settings.REDIS_PASSWORD
        self.port = rag_settings.REDIS_PORT

    def get_client(self) -> redis.Redis:
        return redis.Redis(
            host=self.host,
            username=self.username,
            password=self.password,
            ssl=False,
            port=self.port,
            decode_responses=True
        )


redis_client = RedisConfig().get_client()
