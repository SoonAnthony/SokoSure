from pydantic import BaseModel
from uuid import UUID
from datetime import datetime

from app.features.users.models import BusinessType, IncomeBracket, PaymentFrequency, County


class UserBase(BaseModel):
    national_id: str
    phone_no: str
    full_name: str
    county: County
    business_type: BusinessType
    income_bracket: IncomeBracket
    payment_frequency: PaymentFrequency


class UserCreate(UserBase):
    pin: str  # plain 4-digit PIN from USSD input, hashed in services.py


class UserRead(UserBase):
    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    phone_no: str
    pin: str