import uuid
from typing import Optional
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, asc, desc
from sqlalchemy.orm import Session, selectinload

from app.db.session import get_db
from app.models.booking import Booking
from app.models.user import User
from app.models.enums import UserRole, BookingStatus, EventType, PaymentStatus
from app.schemas.booking import (
    BookingCreate, BookingUpdate, BookingOut, BookingDetailOut,
    BookingStatusUpdate, PaymentStatusUpdate,
)
from app.schemas.common import PaginatedResponse
from app.api.deps import get_current_user, get_optional_current_user, require_min_role
from app.services.booking_service import add_timeline_event, is_valid_transition, new_booking_reference
from app.services.notification_service import log_whatsapp_notification, notify_admin_booking, build_admin_whatsapp_links

router = APIRouter()

SORTABLE_FIELDS = {
    "created_at": Booking.created_at,
    "event_date": Booking.event_date,
    "customer_name": Booking.customer_name,
    "status": Booking.status,
}


@router.post("/", response_model=BookingOut, status_code=201)
def create_booking(
    payload: BookingCreate,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
):
    """
    Public endpoint (guests can submit a booking request without an account).
    If the requester IS logged in as a customer, the booking is linked to
    their account automatically.
    """
    booking = Booking(
        reference_no=new_booking_reference(),
        customer_id=current_user.id if current_user and current_user.role == UserRole.CUSTOMER else None,
        customer_name=payload.customer_name,
        phone=payload.phone,
        email=payload.email,
        city=payload.city,
        venue=payload.venue,
        event_type=payload.event_type,
        event_date=payload.event_date,
        budget=payload.budget,
        decoration_type=payload.decoration_type,
        lighting_type=payload.lighting_type,
        pixel_requirement=payload.pixel_requirement,
        special_notes=payload.special_notes,
        status=BookingStatus.NEW,
        payment_status=PaymentStatus.UNPAID,
    )
    db.add(booking)
    db.flush()

    add_timeline_event(
        db, booking, event_type="system", title="Booking submitted",
        description=f"Booking {booking.reference_no} created via {'account' if current_user else 'guest form'}.",
        actor_id=current_user.id if current_user else None,
    )

    # Queue an internal WhatsApp deep link so staff can confirm receipt with the customer
    log_whatsapp_notification(
        db, booking.id, booking.phone,
        message=(
            f"Hi {booking.customer_name}, thanks for your booking request with GOLD Px "
            f"(Ref: {booking.reference_no}) for your {booking.event_type.value} on {booking.event_date}. "
            f"Our team will reach out shortly with a quotation."
        ),
    )

    message = (
        f"New GOLD Px booking request\n"
        f"Reference: {booking.reference_no}\n"
        f"Name: {booking.customer_name}\n"
        f"Phone: {booking.phone}\n"
        f"Email: {booking.email or 'N/A'}\n"
        f"City: {booking.city}\n"
        f"Venue: {booking.venue}\n"
        f"Event: {booking.event_type.value}\n"
        f"Date: {booking.event_date}\n"
        f"Budget: {booking.budget or 'N/A'}\n"
        f"Notes: {booking.special_notes or 'N/A'}"
    )
    notify_admin_booking(db, booking.id, f"GOLD Px booking request {booking.reference_no}", message)
    build_admin_whatsapp_links(message)

    db.commit()
    db.refresh(booking)
    return booking


@router.get("/", response_model=PaginatedResponse[BookingOut])
def list_bookings(
    status_filter: Optional[BookingStatus] = Query(default=None, alias="status"),
    payment_status: Optional[PaymentStatus] = None,
    event_type: Optional[EventType] = None,
    city: Optional[str] = None,
    event_date_from: Optional[date] = None,
    event_date_to: Optional[date] = None,
    search: Optional[str] = Query(default=None, description="Search customer name, phone, email or reference no"),
    sort_by: str = Query(default="created_at"),
    sort_dir: str = Query(default="desc", pattern="^(asc|desc)$"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_min_role(UserRole.STAFF)),
):
    stmt = select(Booking)

    if status_filter:
        stmt = stmt.where(Booking.status == status_filter)
    if payment_status:
        stmt = stmt.where(Booking.payment_status == payment_status)
    if event_type:
        stmt = stmt.where(Booking.event_type == event_type)
    if city:
        stmt = stmt.where(Booking.city.ilike(f"%{city}%"))
    if event_date_from:
        stmt = stmt.where(Booking.event_date >= event_date_from)
    if event_date_to:
        stmt = stmt.where(Booking.event_date <= event_date_to)
    if search:
        like = f"%{search}%"
        stmt = stmt.where(
            Booking.customer_name.ilike(like) | Booking.phone.ilike(like) |
            Booking.email.ilike(like) | Booking.reference_no.ilike(like)
        )

    total = db.scalar(select(func.count()).select_from(stmt.subquery()))

    order_col = SORTABLE_FIELDS.get(sort_by, Booking.created_at)
    stmt = stmt.order_by(desc(order_col) if sort_dir == "desc" else asc(order_col))
    stmt = stmt.offset((page - 1) * page_size).limit(page_size)

    items = db.scalars(stmt).all()
    return PaginatedResponse.build(items=items, total=total, page=page, page_size=page_size)


@router.get("/my", response_model=PaginatedResponse[BookingOut])
def list_my_bookings(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Customer-facing: see only their own bookings."""
    stmt = select(Booking).where(Booking.customer_id == current_user.id)
    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    items = db.scalars(
        stmt.order_by(Booking.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    ).all()
    return PaginatedResponse.build(items=items, total=total, page=page, page_size=page_size)


def _get_booking_or_404(db: Session, booking_id: uuid.UUID) -> Booking:
    booking = db.scalar(
        select(Booking)
        .options(selectinload(Booking.attachments), selectinload(Booking.timeline_events))
        .where(Booking.id == booking_id)
    )
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    return booking


def _assert_can_view(booking: Booking, current_user: User):
    if current_user.role in (UserRole.STAFF, UserRole.MANAGER, UserRole.ADMIN, UserRole.SUPER_ADMIN):
        return
    if booking.customer_id != current_user.id:
        raise HTTPException(status_code=403, detail="You do not have access to this booking")


@router.get("/{booking_id}", response_model=BookingDetailOut)
def get_booking(booking_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    booking = _get_booking_or_404(db, booking_id)
    _assert_can_view(booking, current_user)
    return booking


@router.patch("/{booking_id}", response_model=BookingOut)
def update_booking(
    booking_id: uuid.UUID,
    payload: BookingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_min_role(UserRole.STAFF)),
):
    booking = _get_booking_or_404(db, booking_id)
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(booking, field, value)

    add_timeline_event(
        db, booking, event_type="note", title="Booking details updated",
        description=", ".join(update_data.keys()) if update_data else None,
        actor_id=current_user.id,
    )
    db.commit()
    db.refresh(booking)
    return booking


@router.patch("/{booking_id}/status", response_model=BookingOut)
def update_booking_status(
    booking_id: uuid.UUID,
    payload: BookingStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_min_role(UserRole.STAFF)),
):
    booking = _get_booking_or_404(db, booking_id)

    if not is_valid_transition(booking.status, payload.status):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot transition booking from '{booking.status.value}' to '{payload.status.value}'",
        )

    old_status = booking.status
    booking.status = payload.status

    add_timeline_event(
        db, booking, event_type="status_change",
        title=f"Status changed: {old_status.value} \u2192 {payload.status.value}",
        description=payload.note, actor_id=current_user.id,
    )

    if payload.status == BookingStatus.APPROVED:
        log_whatsapp_notification(
            db, booking.id, booking.phone,
            message=f"Great news {booking.customer_name}! Your booking {booking.reference_no} has been approved by GOLD Px.",
        )

    db.commit()
    db.refresh(booking)
    return booking


@router.patch("/{booking_id}/payment-status", response_model=BookingOut)
def update_payment_status(
    booking_id: uuid.UUID,
    payload: PaymentStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_min_role(UserRole.STAFF)),
):
    booking = _get_booking_or_404(db, booking_id)
    booking.payment_status = payload.payment_status

    add_timeline_event(
        db, booking, event_type="payment",
        title=f"Payment status changed to {payload.payment_status.value}",
        actor_id=current_user.id,
    )
    db.commit()
    db.refresh(booking)
    return booking


@router.delete("/{booking_id}", status_code=204)
def cancel_booking(
    booking_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_min_role(UserRole.MANAGER)),
):
    booking = _get_booking_or_404(db, booking_id)
    booking.status = BookingStatus.CANCELLED
    add_timeline_event(db, booking, event_type="status_change", title="Booking cancelled", actor_id=current_user.id)
    db.commit()
    return None
