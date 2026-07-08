from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from typing import List

from app.features.claims.models import ClaimCategory, ClaimStatus


class ClaimCreate(BaseModel):
    policy_id: UUID
    category: ClaimCategory
    description: str = Field(max_length=50)


class ClaimRead(BaseModel):
    id: UUID
    claim_code: str
    category: ClaimCategory
    description: str
    status: ClaimStatus
    filed_at: datetime

    class Config:
        from_attributes = True


class ClaimStatusUpdate(BaseModel):
    status: ClaimStatus


class ClaimListResponse(BaseModel):
    claims: List[ClaimRead]