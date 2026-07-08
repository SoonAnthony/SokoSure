from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional

from app.features.policies.models import PolicyStatus
from app.features.users.models import PaymentFrequency


class PolicyCreate(BaseModel):
    user_id: UUID
    recommendation_id: UUID
    coverage_amount: float
    premium_amount: float
    premium_frequency: PaymentFrequency


class PolicyRead(BaseModel):
    id: UUID
    policy_code: str
    status: PolicyStatus
    coverage_amount: float
    premium_amount: float
    premium_frequency: PaymentFrequency
    activated_at: Optional[datetime]
    expires_at: Optional[datetime]

    class Config:
        from_attributes = True