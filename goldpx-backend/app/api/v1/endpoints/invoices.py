import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db.session import get_db
from app.models.booking import Booking
from app.models.invoice import Invoice, Payment
from app.models.user import User
from app.models.enums import UserRole, InvoiceStatus, PaymentStatus
from app.schemas.invoice import InvoiceCreate, InvoiceOut, PaymentCreate, PaymentOut
from app.api.deps import get_current_user, require_min_role
from app.services.booking_service import add_timeline_event
from app.utils.reference import generate_reference

router = APIRouter()


def _get_booking_or_404(db: Session, booking_id: uuid.UUID) -> Booking:
    booking = db.get(Booking, booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    return booking


@router.post("/{booking_id}/invoices", response_model=InvoiceOut, status_code=201)
def create_invoice(
    booking_id: uuid.UUID,
    payload: InvoiceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_min_role(UserRole.STAFF)),
):
    booking = _get_booking_or_404(db, booking_id)

    invoice = Invoice(
        invoice_no=generate_reference("INV"),
        booking_id=booking.id,
        quotation_id=payload.quotation_id,
        status=InvoiceStatus.ISSUED,
        amount_due=payload.amount_due,
        due_date=payload.due_date,
        notes=payload.notes,
        issued_at=datetime.now(timezone.utc),
    )
    db.add(invoice)

    add_timeline_event(
        db, booking, event_type="payment", title=f"Invoice {invoice.invoice_no} issued",
        description=f"Amount due: {payload.amount_due}", actor_id=current_user.id,
    )
    db.commit()
    db.refresh(invoice)
    return invoice


@router.get("/{booking_id}/invoices", response_model=list[InvoiceOut])
def list_invoices(booking_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    booking = _get_booking_or_404(db, booking_id)
    is_staff = current_user.role in (UserRole.STAFF, UserRole.MANAGER, UserRole.ADMIN, UserRole.SUPER_ADMIN)
    if not is_staff and booking.customer_id != current_user.id:
        raise HTTPException(status_code=403, detail="You do not have access to this booking's invoices")

    invoices = db.scalars(
        select(Invoice).where(Invoice.booking_id == booking_id).order_by(Invoice.created_at.desc())
    ).all()
    return invoices


@router.post("/{booking_id}/invoices/{invoice_id}/payments", response_model=PaymentOut, status_code=201)
def record_payment(
    booking_id: uuid.UUID,
    invoice_id: uuid.UUID,
    payload: PaymentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_min_role(UserRole.STAFF)),
):
    booking = _get_booking_or_404(db, booking_id)
    invoice = db.get(Invoice, invoice_id)
    if not invoice or invoice.booking_id != booking_id:
        raise HTTPException(status_code=404, detail="Invoice not found")

    payment = Payment(
        invoice_id=invoice.id,
        amount=payload.amount,
        method=payload.method,
        reference=payload.reference,
        paid_at=payload.paid_at or datetime.now(timezone.utc),
        recorded_by_id=current_user.id,
    )
    db.add(payment)

    invoice.amount_paid = float(invoice.amount_paid) + payload.amount
    if invoice.amount_paid >= invoice.amount_due:
        invoice.status = InvoiceStatus.PAID
        booking.payment_status = PaymentStatus.PAID
    else:
        booking.payment_status = PaymentStatus.PARTIALLY_PAID

    add_timeline_event(
        db, booking, event_type="payment",
        title=f"Payment of {payload.amount} recorded ({payload.method})",
        actor_id=current_user.id,
    )

    db.commit()
    db.refresh(payment)
    return payment
