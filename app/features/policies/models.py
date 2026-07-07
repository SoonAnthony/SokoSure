from sqlmodel import SQLModel, Field
from uuid import UUID, uuid4
from enum import Enum
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, DateTime, func

from app.features.users.models import PaymentFrequency


class PolicyStatus(str, Enum):
    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"


class Policy(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="user.id", index=True)
    recommendation_id: UUID = Field(foreign_key="policyrecommendation.id")

    policy_code: str = Field(unique=True, index=True)  # e.g. SK34252
    status: PolicyStatus = Field(default=PolicyStatus.PENDING, index=True)

    coverage_amount: float
    premium_amount: float
    premium_frequency: PaymentFrequency

    activated_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None

    created_at: Optional[datetime] = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )