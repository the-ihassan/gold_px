import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session

from app.models.notification import NotificationLog
from app.models.enums import NotificationChannel, NotificationStatus
from app.services.whatsapp_service import build_customer_whatsapp_link


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
