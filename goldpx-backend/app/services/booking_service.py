import uuid
from typing import Optional
from sqlalchemy.orm import Session

from app.models.booking import Booking, BookingTimelineEvent
from app.models.enums import BookingStatus
from app.utils.reference import generate_reference


VALID_TRANSITIONS = {
    BookingStatus.NEW: {BookingStatus.UNDER_REVIEW, BookingStatus.CANCELLED},
    BookingStatus.UNDER_REVIEW: {BookingStatus.QUOTATION_SENT, BookingStatus.CANCELLED},
    BookingStatus.QUOTATION_SENT: {BookingStatus.APPROVED, BookingStatus.REJECTED, BookingStatus.CANCELLED},
    BookingStatus.APPROVED: {BookingStatus.IN_PROGRESS, BookingStatus.CANCELLED},
    BookingStatus.REJECTED: {BookingStatus.UNDER_REVIEW, BookingStatus.CANCELLED},
    BookingStatus.IN_PROGRESS: {BookingStatus.COMPLETED, BookingStatus.CANCELLED},
    BookingStatus.COMPLETED: set(),
    BookingStatus.CANCELLED: set(),
}


def is_valid_transition(current: BookingStatus, target: BookingStatus) -> bool:
    if current == target:
        return True
    return target in VALID_TRANSITIONS.get(current, set())


def add_timeline_event(
    db: Session,
    booking: Booking,
    event_type: str,
    title: str,
    description: Optional[str] = None,
    actor_id: Optional[uuid.UUID] = None,
) -> BookingTimelineEvent:
    event = BookingTimelineEvent(
        booking_id=booking.id,
        event_type=event_type,
        title=title,
        description=description,
        actor_id=actor_id,
    )
    db.add(event)
    db.flush()
    return event


def new_booking_reference() -> str:
    return generate_reference("GPX")
