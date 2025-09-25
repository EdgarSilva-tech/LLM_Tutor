# utils/redis_config.py
import redis
from quizz_settings import quizz_settings


class RedisConfig:
    def __init__(self):
        self.host = quizz_settings.REDIS_ENDPOINT
        self.username = quizz_settings.REDIS_USERNAME
        self.password = quizz_settings.REDIS_PASSWORD
        self.port = quizz_settings.REDIS_PORT

    def get_client(self) -> redis.Redis:
        return redis.Redis(
            host=self.host,
            username=self.username,
            password=self.password,
            ssl=False,
            port=self.port,
            decode_responses=True,
        )


redis_client = RedisConfig().get_client()
