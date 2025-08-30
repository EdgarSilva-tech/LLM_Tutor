# utils/redis_config.py
import redis
from eval_settings import eval_settings


class RedisConfig:
    def __init__(self):
        self.host = eval_settings.REDIS_ENDPOINT
        self.username = eval_settings.REDIS_USERNAME
        self.password = eval_settings.REDIS_PASSWORD
        self.port = eval_settings.REDIS_PORT

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
