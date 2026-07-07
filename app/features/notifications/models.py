from sqlmodel import SQLModel, Field
from uuid import UUID, uuid4
from enum import Enum
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, DateTime, func


class SMSDirection(str, Enum):
    INBOUND = "INBOUND"
    OUTBOUND = "OUTBOUND"


class SMSLog(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="user.id", index=True)

    message: str
    direction: SMSDirection = Field(index=True)

    sent_at: Optional[datetime] = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )