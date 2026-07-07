from sqlmodel import SQLModel, Field
from uuid import UUID, uuid4
from enum import Enum
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, DateTime, func


class ClaimCategory(str, Enum):
    FIRE = "FIRE"
    THEFT = "THEFT"
    FLOOD = "FLOOD"
    OTHER = "OTHER"


class ClaimStatus(str, Enum):
    SUBMITTED = "SUBMITTED"
    UNDER_REVIEW = "UNDER_REVIEW"
    APPROVED = "APPROVED"
    DENIED = "DENIED"


class Claim(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    policy_id: UUID = Field(foreign_key="policy.id", index=True)

    category: ClaimCategory
    description: str = Field(max_length=50)
    claim_code: str = Field(unique=True, index=True)  # e.g. CL9832
    status: ClaimStatus = Field(default=ClaimStatus.SUBMITTED, index=True)

    filed_at: Optional[datetime] = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )