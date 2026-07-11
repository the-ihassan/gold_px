import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.notification import NotificationLog
from app.models.user import User
from app.models.enums import UserRole, NotificationChannel, NotificationStatus
from app.api.deps import require_min_role

router = APIRouter()


@router.get("/")
def list_notifications(
    channel: NotificationChannel | None = None,
    status_filter: NotificationStatus | None = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
    _: User = Depends(require_min_role(UserRole.STAFF)),
):
    stmt = select(NotificationLog).order_by(NotificationLog.created_at.desc()).limit(100)
    if channel:
        stmt = stmt.where(NotificationLog.channel == channel)
    if status_filter:
        stmt = stmt.where(NotificationLog.status == status_filter)
    logs = db.scalars(stmt).all()
    return [
        {
            "id": log.id,
            "booking_id": log.booking_id,
            "channel": log.channel.value,
            "status": log.status.value,
            "message": log.message,
            "external_link": log.external_link,
            "created_at": log.created_at,
        }
        for log in logs
    ]


@router.patch("/{notification_id}/mark-sent")
def mark_notification_sent(
    notification_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: User = Depends(require_min_role(UserRole.STAFF)),
):
    """Staff calls this after clicking the wa.me link and actually hitting send."""
    log = db.get(NotificationLog, notification_id)
    if not log:
        raise HTTPException(status_code=404, detail="Notification not found")
    log.status = NotificationStatus.SENT
    log.sent_at = datetime.now(timezone.utc)
    db.commit()
    return {"message": "Marked as sent"}
