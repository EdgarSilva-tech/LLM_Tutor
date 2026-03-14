import resend  # type: ignore[import-not-found]
from fastapi import HTTPException

from .data_models import EmailRequest, EmailResponse
from .logger import get_logger
from .settings import settings

logger = get_logger(__name__)
resend.api_key = settings.RESEND_API_KEY


async def send_email(email_request: EmailRequest) -> EmailResponse:
    try:
        response = resend.Emails.send(
            {
                "from": "LLM Academy <onboarding@resend.dev>",
                "to": [email_request.to],
                "subject": email_request.subject,
                "html": email_request.html,
            }
        )
        return EmailResponse(success=True, id=response["id"])
    except Exception as e:
        logger.error("Error sending email: %s", e)
        raise HTTPException(status_code=500, detail=f"Error sending email: {e}")
