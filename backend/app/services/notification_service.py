import asyncio
import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.notification import NotificationLog
from app.models.enums import NotificationChannel, NotificationStatus
from app.services.email_service import send_email
from app.services.whatsapp_service import build_customer_whatsapp_link, build_business_whatsapp_link


def log_whatsapp_notification(
    db: Session,
    booking_id: uuid.UUID,
    customer_phone: str,
    message: str,
    recipient_user_id: Optional[uuid.UUID] = None,
) -> NotificationLog:
    """
    Creates a WhatsApp deep-link notification record. Since there's no
    Business API key yet, `status` stays PENDING until a staff member
    actually clicks the link and sends it (frontend can PATCH it to SENT).
    """
    link = build_customer_whatsapp_link(customer_phone, message)
    log = NotificationLog(
        booking_id=booking_id,
        recipient_user_id=recipient_user_id,
        channel=NotificationChannel.WHATSAPP,
        status=NotificationStatus.PENDING,
        message=message,
        external_link=link,
    )
    db.add(log)
    db.flush()
    return log


def notify_admin_booking(db: Session, booking_id: Optional[uuid.UUID], subject: str, message: str) -> bool:
    recipients = [email.strip() for email in getattr(settings, "ADMIN_NOTIFICATION_EMAILS", "ihassan.dev@outlook.com").split(",") if email.strip()]
    try:
        sent = asyncio.run(send_email(recipients, subject, message))
    except Exception as exc:
        sent = False
        log_email_notification(db, booking_id, subject, message, False, error=str(exc))
        return False

    log_email_notification(db, booking_id, subject, message, sent)
    return sent


def build_admin_whatsapp_links(message: str) -> list[str]:
    numbers = [
        number.strip()
        for number in getattr(settings, "ADMIN_WHATSAPP_NUMBERS", "923145355656,923335079575").split(",")
        if number.strip()
    ]
    return [build_business_whatsapp_link(message) for _ in numbers]


def log_email_notification(
    db: Session,
    booking_id: Optional[uuid.UUID],
    subject: str,
    message: str,
    sent: bool,
    recipient_user_id: Optional[uuid.UUID] = None,
    error: Optional[str] = None,
) -> NotificationLog:
    log = NotificationLog(
        booking_id=booking_id,
        recipient_user_id=recipient_user_id,
        channel=NotificationChannel.EMAIL,
        status=NotificationStatus.SENT if sent else NotificationStatus.FAILED,
        subject=subject,
        message=message,
        error=error,
        sent_at=datetime.now(timezone.utc) if sent else None,
    )
    db.add(log)
    db.flush()
    return log
