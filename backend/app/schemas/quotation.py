import uuid
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

from app.models.enums import QuotationStatus


class QuotationItemCreate(BaseModel):
    description: str = Field(min_length=2, max_length=500)
    quantity: int = Field(default=1, ge=1)
    unit_price: float = Field(ge=0)


class QuotationCreate(BaseModel):
    items: List[QuotationItemCreate]
    discount: float = Field(default=0, ge=0)
    tax: float = Field(default=0, ge=0)
    valid_until: Optional[datetime] = None
    notes: Optional[str] = None


class QuotationItemOut(BaseModel):
    id: uuid.UUID
    description: str
    quantity: int
    unit_price: float
    line_total: float

    class Config:
        from_attributes = True


class QuotationOut(BaseModel):
    id: uuid.UUID
    quotation_no: str
    booking_id: uuid.UUID
    status: QuotationStatus
    subtotal: float
    discount: float
    tax: float
    total: float
    valid_until: Optional[datetime] = None
    notes: Optional[str] = None
    items: List[QuotationItemOut] = []
    created_at: datetime

    class Config:
        from_attributes = True


class QuotationRespondRequest(BaseModel):
    accept: bool
    rejection_reason: Optional[str] = None
