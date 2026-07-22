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


class SMSSessionState(str, Enum):
    """Steps in the SMS profile-completion conversation."""
    AWAIT_NAME      = "AWAIT_NAME"
    AWAIT_REGION    = "AWAIT_REGION"   # NEW: region picker, shown before county
    AWAIT_COUNTY    = "AWAIT_COUNTY"
    AWAIT_BUSINESS  = "AWAIT_BUSINESS"
    AWAIT_INCOME    = "AWAIT_INCOME"
    AWAIT_FREQUENCY = "AWAIT_FREQUENCY"
    COMPLETE        = "COMPLETE"


class SMSSession(SQLModel, table=True):
    """
    Tracks where a user is in the SMS profile-completion conversation.
    One row per user — updated in place as they reply.
    """
    phone_number: str = Field(primary_key=True)
    state: SMSSessionState = Field(default=SMSSessionState.AWAIT_NAME)

    # Collected profile data, filled step by step
    full_name:  Optional[str] = None
    region:     Optional[str] = None   #holds the chosen region key until county is picked
    county:     Optional[str] = None
    county_page: Optional[int] = None  #tracks pagination position within REGION_COUNTIES[region]
    business:   Optional[str] = None
    income:     Optional[str] = None

    updated_at: Optional[datetime] = Field(
        sa_column=Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
    )