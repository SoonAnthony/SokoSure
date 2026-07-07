from sqlmodel import SQLModel, Field
from uuid import UUID, uuid4
from enum import Enum
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, DateTime, func


class PaymentStatus(str, Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    FAILED = "FAILED"


class PremiumPayment(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    policy_id: UUID = Field(foreign_key="policy.id", index=True)

    amount: float
    provider_transaction_id: str = Field(unique=True, index=True)
    status: PaymentStatus = Field(default=PaymentStatus.PENDING, index=True)

    paid_at: Optional[datetime] = None

    created_at: Optional[datetime] = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )