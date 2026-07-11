from datetime import date, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.booking import Booking
from app.models.invoice import Invoice
from app.models.user import User
from app.models.enums import UserRole, BookingStatus, PaymentStatus, InvoiceStatus
from app.api.deps import require_min_role

router = APIRouter()


@router.get("/summary")
def dashboard_summary(
    db: Session = Depends(get_db),
    _: User = Depends(require_min_role(UserRole.MANAGER)),
):
    today = date.today()

    total_bookings = db.scalar(select(func.count()).select_from(Booking)) or 0
    upcoming_events = db.scalar(
        select(func.count()).select_from(Booking).where(
            Booking.event_date >= today, Booking.status.notin_([BookingStatus.CANCELLED, BookingStatus.COMPLETED])
        )
    ) or 0
    pending_quotations = db.scalar(
        select(func.count()).select_from(Booking).where(Booking.status == BookingStatus.UNDER_REVIEW)
    ) or 0
    pending_payments = db.scalar(
        select(func.count()).select_from(Booking).where(Booking.payment_status != PaymentStatus.PAID)
    ) or 0
    total_revenue = db.scalar(
        select(func.coalesce(func.sum(Invoice.amount_paid), 0)).select_from(Invoice)
    ) or 0

    recent_customers = db.scalars(
        select(Booking).order_by(Booking.created_at.desc()).limit(5)
    ).all()

    bookings_by_status = dict(
        db.execute(select(Booking.status, func.count()).group_by(Booking.status)).all()
    )

    return {
        "total_bookings": total_bookings,
        "upcoming_events": upcoming_events,
        "pending_quotations": pending_quotations,
        "pending_payments": pending_payments,
        "total_revenue": float(total_revenue),
        "bookings_by_status": {k.value if hasattr(k, "value") else k: v for k, v in bookings_by_status.items()},
        "recent_bookings": [
            {"reference_no": b.reference_no, "customer_name": b.customer_name, "status": b.status.value, "created_at": b.created_at}
            for b in recent_customers
        ],
    }


@router.get("/revenue-chart")
def revenue_chart(
    days: int = 30,
    db: Session = Depends(get_db),
    _: User = Depends(require_min_role(UserRole.MANAGER)),
):
    start_date = date.today() - timedelta(days=days)
    rows = db.execute(
        select(func.date(Invoice.issued_at), func.coalesce(func.sum(Invoice.amount_paid), 0))
        .where(Invoice.issued_at >= start_date)
        .group_by(func.date(Invoice.issued_at))
        .order_by(func.date(Invoice.issued_at))
    ).all()
    return {"series": [{"date": str(r[0]), "revenue": float(r[1])} for r in rows]}
