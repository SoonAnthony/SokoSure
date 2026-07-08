# app/features/ussd/routes.py

from fastapi import APIRouter, Form

from .services import USSDService

router = APIRouter(prefix="/ussd", tags=["USSD"])

ussd_service = USSDService()


@router.post("")
async def ussd_callback(
    sessionId: str = Form(...),
    serviceCode: str = Form(...),
    phoneNumber: str = Form(...),
    text: str = Form(...)
):
    return await ussd_service.handle(
        sessionId=sessionId,
        serviceCode=serviceCode,
        phoneNumber=phoneNumber,
        text=text,
    )