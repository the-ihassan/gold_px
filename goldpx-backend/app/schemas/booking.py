import uuid
from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field

from app.models.enums import (
    EventType, DecorationType, LightingType, BookingStatus, PaymentStatus,
)


class BookingCreate(BaseModel):
    customer_name: str = Field(min_length=2, max_length=150)
    phone: str = Field(min_length=7, max_length=20)
    email: Optional[EmailStr] = None
    city: str = Field(min_length=2, max_length=100)
    venue: str = Field(min_length=2, max_length=255)
    event_type: EventType
    event_date: date
    budget: Optional[float] = Field(default=None, ge=0)
    decoration_type: Optional[DecorationType] = None
    lighting_type: Optional[LightingType] = None
    pixel_requirement: Optional[str] = None
    special_notes: Optional[str] = None


class BookingUpdate(BaseModel):
    customer_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    city: Optional[str] = None
    venue: Optional[str] = None
    event_type: Optional[EventType] = None
    event_date: Optional[date] = None
    budget: Optional[float] = None
    decoration_type: Optional[DecorationType] = None
    lighting_type: Optional[LightingType] = None
    pixel_requirement: Optional[str] = None
    special_notes: Optional[str] = None
    assigned_staff_id: Optional[uuid.UUID] = None


class BookingStatusUpdate(BaseModel):
    status: BookingStatus
    note: Optional[str] = None


class PaymentStatusUpdate(BaseModel):
    payment_status: PaymentStatus


class BookingAttachmentOut(BaseModel):
    id: uuid.UUID
    file_url: str
    file_name: str
    file_type: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class BookingTimelineEventOut(BaseModel):
    id: uuid.UUID
    event_type: str
    title: str
    description: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class BookingOut(BaseModel):
    id: uuid.UUID
    reference_no: str
    customer_id: Optional[uuid.UUID] = None
    customer_name: str
    phone: str
    email: Optional[str] = None
    city: str
    venue: str
    event_type: EventType
    event_date: date
    budget: Optional[float] = None
    decoration_type: Optional[DecorationType] = None
    lighting_type: Optional[LightingType] = None
    pixel_requirement: Optional[str] = None
    special_notes: Optional[str] = None
    status: BookingStatus
    payment_status: PaymentStatus
    assigned_staff_id: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BookingDetailOut(BookingOut):
    attachments: List[BookingAttachmentOut] = []
    timeline_events: List[BookingTimelineEventOut] = []
