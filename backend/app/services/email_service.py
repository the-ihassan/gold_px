import logging
from typing import List

from app.core.config import settings

logger = logging.getLogger("goldpx.email")


def _smtp_configured() -> bool:
    return bool(settings.SMTP_HOST and settings.SMTP_USER and settings.SMTP_PASSWORD)


async def send_email(to: List[str], subject: str, body: str) -> bool:
    """
    Sends an email via SMTP if configured; otherwise logs and returns False
    so callers can decide whether to surface a warning. This keeps the API
    usable in dev/staging before real SMTP credentials are supplied.
    """
    if not _smtp_configured():
        logger.warning("SMTP not configured - email NOT sent. To=%s Subject=%s", to, subject)
        return False

    from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType

    conf = ConnectionConfig(
        MAIL_USERNAME=settings.SMTP_USER,
        MAIL_PASSWORD=settings.SMTP_PASSWORD,
        MAIL_FROM=settings.SMTP_FROM_EMAIL,
        MAIL_FROM_NAME=settings.SMTP_FROM_NAME,
        MAIL_PORT=settings.SMTP_PORT,
        MAIL_SERVER=settings.SMTP_HOST,
        MAIL_STARTTLS=True,
        MAIL_SSL_TLS=False,
        USE_CREDENTIALS=True,
    )
    message = MessageSchema(subject=subject, recipients=to, body=body, subtype=MessageType.html)
    fm = FastMail(conf)
    await fm.send_message(message)
    return True
