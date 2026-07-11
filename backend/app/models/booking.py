import uuid
from datetime import date, datetime
from typing import Optional, List

from sqlalchemy import String, Text, Date, Numeric, ForeignKey, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base
from app.models.enums import (
    EventType, DecorationType, LightingType, BookingStatus, PaymentStatus,
)


class Booking(Base):
    # Human-friendly reference, e.g. GPX-2026-000123
    reference_no: Mapped[str] = mapped_column(String(30), unique=True, index=True, nullable=False)

    # Customer info (denormalized snapshot at booking time, so historical
    # bookings stay accurate even if the customer later edits their profile)
    customer_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    customer_name: Mapped[str] = mapped_column(String(150), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    city: Mapped[str] = mapped_column(String(100), nullable=False)

    venue: Mapped[str] = mapped_column(String(255), nullable=False)
    event_type: Mapped[EventType] = mapped_column(SAEnum(EventType, name="event_type"), nullable=False)
    event_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)

    budget: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)

    decoration_type: Mapped[Optional[DecorationType]] = mapped_column(
        SAEnum(DecorationType, name="decoration_type"), nullable=True
    )
    lighting_type: Mapped[Optional[LightingType]] = mapped_column(
        SAEnum(LightingType, name="lighting_type"), nullable=True
    )
    pixel_requirement: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    special_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    status: Mapped[BookingStatus] = mapped_column(
        SAEnum(BookingStatus, name="booking_status"), default=BookingStatus.NEW, nullable=False, index=True
    )
    payment_status: Mapped[PaymentStatus] = mapped_column(
        SAEnum(PaymentStatus, name="payment_status"), default=PaymentStatus.UNPAID, nullable=False, index=True
    )

    assigned_staff_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )

    # ---- relationships ----
    customer: Mapped[Optional["User"]] = relationship(
        "User", back_populates="bookings", foreign_keys=[customer_id]
    )
    attachments: Mapped[List["BookingAttachment"]] = relationship(
        "BookingAttachment", back_populates="booking", cascade="all, delete-orphan"
    )
    timeline_events: Mapped[List["BookingTimelineEvent"]] = relationship(
        "BookingTimelineEvent", back_populates="booking", cascade="all, delete-orphan",
        order_by="BookingTimelineEvent.created_at",
    )
    quotations: Mapped[List["Quotation"]] = relationship(
        "Quotation", back_populates="booking", cascade="all, delete-orphan"
    )
    invoices: Mapped[List["Invoice"]] = relationship(
        "Invoice", back_populates="booking", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Booking {self.reference_no} {self.status}>"


class BookingAttachment(Base):
    booking_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("bookings.id"), nullable=False)
    file_url: Mapped[str] = mapped_column(String(1000), nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    uploaded_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    booking: Mapped["Booking"] = relationship("Booking", back_populates="attachments")


class BookingTimelineEvent(Base):
    """Audit trail of everything that happens to a booking (status changes,
    quotation sent, payment received, notes, etc.) - powers the Timeline UI."""
    booking_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("bookings.id"), nullable=False)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)  # status_change | note | payment | quotation | system
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    actor_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    booking: Mapped["Booking"] = relationship("Booking", back_populates="timeline_events")
