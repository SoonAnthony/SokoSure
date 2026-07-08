from pydantic import BaseModel
from uuid import UUID
from datetime import datetime


class RecommendationBase(BaseModel):
    recommended_plan: str
    premium: float
    coverage: float
    reason: str


class RecommendationCreate(RecommendationBase):
    user_id: UUID


class RecommendationRead(RecommendationBase):
    id: UUID
    user_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True