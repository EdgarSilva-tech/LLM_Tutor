# utils/redis_config.py
import redis
from .la_settings import la_settings


class RedisConfig:
    def __init__(self):
        self.host = la_settings.REDIS_ENDPOINT
        self.username = la_settings.REDIS_USERNAME
        self.password = la_settings.REDIS_PASSWORD
        self.port = la_settings.REDIS_PORT

    def get_client(self) -> redis.Redis:
        return redis.Redis(
            host=self.host,
            username=self.username,
            password=self.password,
            ssl=False,
            port=self.port,
            decode_responses=True,
            socket_connect_timeout=2,
            socket_timeout=2,
            retry_on_timeout=True,
            health_check_interval=30,
        )


redis_client = RedisConfig().get_client()
