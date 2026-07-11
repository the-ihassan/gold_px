import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db.session import get_db
from app.models.booking import Booking
from app.models.quotation import Quotation, QuotationItem
from app.models.user import User
from app.models.enums import UserRole, QuotationStatus, BookingStatus
from app.schemas.quotation import QuotationCreate, QuotationOut, QuotationRespondRequest
from app.api.deps import get_current_user, require_min_role
from app.services.booking_service import add_timeline_event, is_valid_transition
from app.services.notification_service import log_whatsapp_notification
from app.utils.reference import generate_reference

router = APIRouter()


def _get_booking_or_404(db: Session, booking_id: uuid.UUID) -> Booking:
    booking = db.get(Booking, booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    return booking


@router.post("/{booking_id}/quotations", response_model=QuotationOut, status_code=201)
def create_quotation(
    booking_id: uuid.UUID,
    payload: QuotationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_min_role(UserRole.STAFF)),
):
    booking = _get_booking_or_404(db, booking_id)

    subtotal = sum(item.quantity * item.unit_price for item in payload.items)
    total = max(subtotal - payload.discount + payload.tax, 0)

    quotation = Quotation(
        quotation_no=generate_reference("QTN"),
        booking_id=booking.id,
        status=QuotationStatus.SENT,
        subtotal=subtotal,
        discount=payload.discount,
        tax=payload.tax,
        total=total,
        valid_until=payload.valid_until,
        notes=payload.notes,
        created_by_id=current_user.id,
    )
    db.add(quotation)
    db.flush()

    for item in payload.items:
        db.add(QuotationItem(
            quotation_id=quotation.id,
            description=item.description,
            quantity=item.quantity,
            unit_price=item.unit_price,
            line_total=item.quantity * item.unit_price,
        ))

    if is_valid_transition(booking.status, BookingStatus.QUOTATION_SENT):
        booking.status = BookingStatus.QUOTATION_SENT

    add_timeline_event(
        db, booking, event_type="quotation",
        title=f"Quotation {quotation.quotation_no} sent",
        description=f"Total: {total}", actor_id=current_user.id,
    )

    log_whatsapp_notification(
        db, booking.id, booking.phone,
        message=(
            f"Hi {booking.customer_name}, your quotation {quotation.quotation_no} for "
            f"GOLD Px booking {booking.reference_no} is ready. Total: PKR {total:,.0f}. "
            f"Please review and let us know if you'd like to proceed."
        ),
    )

    db.commit()
    db.refresh(quotation)
    return quotation


@router.get("/{booking_id}/quotations", response_model=list[QuotationOut])
def list_quotations(booking_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    booking = _get_booking_or_404(db, booking_id)
    is_staff = current_user.role in (UserRole.STAFF, UserRole.MANAGER, UserRole.ADMIN, UserRole.SUPER_ADMIN)
    if not is_staff and booking.customer_id != current_user.id:
        raise HTTPException(status_code=403, detail="You do not have access to this booking's quotations")

    quotations = db.scalars(
        select(Quotation).options(selectinload(Quotation.items))
        .where(Quotation.booking_id == booking_id).order_by(Quotation.created_at.desc())
    ).all()
    return quotations


@router.post("/{booking_id}/quotations/{quotation_id}/respond", response_model=QuotationOut)
def respond_to_quotation(
    booking_id: uuid.UUID,
    quotation_id: uuid.UUID,
    payload: QuotationRespondRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Customer accepts or rejects a quotation - drives the approval workflow."""
    booking = _get_booking_or_404(db, booking_id)
    if booking.customer_id != current_user.id and current_user.role == UserRole.CUSTOMER:
        raise HTTPException(status_code=403, detail="You do not have access to this booking")

    quotation = db.get(Quotation, quotation_id)
    if not quotation or quotation.booking_id != booking_id:
        raise HTTPException(status_code=404, detail="Quotation not found")

    if quotation.status != QuotationStatus.SENT:
        raise HTTPException(status_code=400, detail=f"Quotation is already '{quotation.status.value}'")

    quotation.responded_at = datetime.now(timezone.utc)

    if payload.accept:
        quotation.status = QuotationStatus.ACCEPTED
        if is_valid_transition(booking.status, BookingStatus.APPROVED):
            booking.status = BookingStatus.APPROVED
        add_timeline_event(db, booking, event_type="quotation", title="Quotation accepted by customer", actor_id=current_user.id)
    else:
        quotation.status = QuotationStatus.REJECTED
        quotation.rejection_reason = payload.rejection_reason
        if is_valid_transition(booking.status, BookingStatus.REJECTED):
            booking.status = BookingStatus.REJECTED
        add_timeline_event(
            db, booking, event_type="quotation", title="Quotation rejected by customer",
            description=payload.rejection_reason, actor_id=current_user.id,
        )

    db.commit()
    db.refresh(quotation)
    return quotation
