# app/features/ussd/schemas.py

from pydantic import BaseModel


class USSDRequest(BaseModel):
    sessionId: str
    serviceCode: str
    phoneNumber: str
    text: str