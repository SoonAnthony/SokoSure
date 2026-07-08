from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional

from app.features.payments.models import PaymentStatus


class PaymentWebhookPayload(BaseModel):
    policy_id: UUID
    amount: float
    provider_transaction_id: str
    status: PaymentStatus


class PaymentRead(BaseModel):
    id: UUID
    policy_id: UUID
    amount: float
    status: PaymentStatus
    paid_at: Optional[datetime]

    class Config:
        from_attributes = True