# app/features/ussd/models.py

from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime
from sqlalchemy import Column, DateTime, func


class USSDSession(SQLModel, table=True):
    """
    Persists a user's position in the USSD state machine across requests.
    Africa's Talking sends the same sessionId for every step of a session.
    """
    session_id:   str = Field(primary_key=True)   # Africa's Talking sessionId
    phone_number: str = Field(index=True)          # caller's MSISDN
    state:        str = Field(default="MAIN_MENU") # current USSDState value

    # Temporary registration data collected step-by-step
    national_id:  Optional[str] = None
    full_name:    Optional[str] = None
    pin:          Optional[str] = None             # plain PIN, cleared after hashing
    county:       Optional[str] = None
    business:     Optional[str] = None
    income:       Optional[str] = None
    frequency:    Optional[str] = None

    # Temporary claim data
    claim_type:   Optional[str] = None

    # Authenticated user id (set after successful login)
    user_id:      Optional[str] = None

    updated_at: Optional[datetime] = Field(
        sa_column=Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
    )
