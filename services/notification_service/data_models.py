from pydantic import BaseModel
from datetime import datetime


class EmailRequest(BaseModel):
    to: str
    subject: str
    html: str
    scheduled_at: datetime | None = None


class EmailResponse(BaseModel):
    """Response after sending email."""

    success: bool
    id: str
