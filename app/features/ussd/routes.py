# app/features/ussd/routes.py

from fastapi import APIRouter, Depends, Form
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.features.ussd.services import USSDService

router = APIRouter(prefix="/ussd", tags=["USSD"])

ussd_service = USSDService()


@router.post("")
async def ussd_callback(
    sessionId:   str = Form(...),
    serviceCode: str = Form(...),
    phoneNumber: str = Form(...),
    text:        str = Form(default=""),  # AT sends empty string on first dial
    db: AsyncSession = Depends(get_session),
):
    """
    Africa's Talking posts to this endpoint on every USSD interaction.
    We keep the route thin — all logic lives in USSDService.
    """
    return await ussd_service.handle_request(
        db=db,
        session_id=sessionId,
        phone_number=phoneNumber,
        text=text,
    )
