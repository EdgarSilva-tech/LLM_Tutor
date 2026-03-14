from typing import Any, Dict

from .la_settings import la_settings
from .quizz_create_publish import _publish_with_retry


async def publish_notification_email_request(
    payload: Dict[str, Any], delay: int = 0
) -> None:
    await _publish_with_retry(
        payload,
        la_settings.RABBITMQ_ROUTING_KEY_NOTIFICATION,
        delay=delay,
    )
