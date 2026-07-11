import uuid
from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, Field

from app.models.enums import InvoiceStatus


class InvoiceCreate(BaseModel):
    quotation_id: Optional[uuid.UUID] = None
    amount_due: float = Field(gt=0)
    due_date: Optional[date] = None
    notes: Optional[str] = None


class InvoiceOut(BaseModel):
    id: uuid.UUID
    invoice_no: str
    booking_id: uuid.UUID
    quotation_id: Optional[uuid.UUID] = None
    status: InvoiceStatus
    amount_due: float
    amount_paid: float
    balance: float
    due_date: Optional[date] = None
    issued_at: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class PaymentCreate(BaseModel):
    amount: float = Field(gt=0)
    method: str = Field(min_length=2, max_length=50)
    reference: Optional[str] = None
    paid_at: Optional[datetime] = None


class PaymentOut(BaseModel):
    id: uuid.UUID
    invoice_id: uuid.UUID
    amount: float
    method: str
    reference: Optional[str] = None
    paid_at: datetime

    class Config:
        from_attributes = True
