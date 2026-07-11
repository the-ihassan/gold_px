import asyncio
import logging

from app.core.celery_app import celery_app
from app.services.email_service import send_email

logger = logging.getLogger("goldpx.tasks")


@celery_app.task(name="send_email_task", bind=True, max_retries=3, default_retry_delay=30)
def send_email_task(self, to: list, subject: str, body: str):
    """Runs email sending in the background via Celery worker."""
    try:
        return asyncio.run(send_email(to=to, subject=subject, body=body))
    except Exception as exc:  # noqa: BLE001
        logger.exception("send_email_task failed")
        raise self.retry(exc=exc)


@celery_app.task(name="ping")
def ping():
    return "pong"
