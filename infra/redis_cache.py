# utils/redis_config.py
import redis
from settings import settings


class RedisConfig:
    def __init__(self):
        self.host = settings.REDIS_ENDPOINT
        self.username = settings.REDIS_USERNAME
        self.password = settings.REDIS_PASSWORD
        self.port = settings.REDIS_PORT

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
