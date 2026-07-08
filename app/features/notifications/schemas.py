from pydantic import BaseModel
from uuid import UUID


class SMSSend(BaseModel):
    user_id: UUID
    message: str