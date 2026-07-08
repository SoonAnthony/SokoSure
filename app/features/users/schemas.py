from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional

from app.features.users.models import BusinessType, IncomeBracket, PaymentFrequency, County


class UserCreateUSSD(BaseModel):
    """Minimal schema used during USSD registration (3 steps only)."""
    national_id: str
    phone_no: str
    pin: str


class UserCompleteProfile(BaseModel):
    """Schema for completing the profile after USSD registration via SMS/web."""
    full_name: str
    county: County
    business_type: BusinessType
    income_bracket: IncomeBracket
    payment_frequency: PaymentFrequency


class UserCreate(UserCreateUSSD):
    """Full creation schema (used by REST API / admin)."""
    full_name: Optional[str] = None
    county: Optional[County] = None
    business_type: Optional[BusinessType] = None
    income_bracket: Optional[IncomeBracket] = None
    payment_frequency: Optional[PaymentFrequency] = None


class UserRead(BaseModel):
    id: UUID
    national_id: str
    phone_no: str
    full_name: Optional[str]
    county: Optional[County]
    business_type: Optional[BusinessType]
    income_bracket: Optional[IncomeBracket]
    payment_frequency: Optional[PaymentFrequency]
    created_at: datetime

    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    phone_no: str
    pin: str