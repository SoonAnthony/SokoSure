from pydantic import BaseModel, field_validator
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
    @field_validator("pin")
    @classmethod
    def validate_pin(cls, v):
        if not v.isdigit() or len(v) != 4:
            raise ValueError("PIN must be exactly 4 digits")
        return v

class UserRead(UserBase):
    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    phone_no: str
    pin: str