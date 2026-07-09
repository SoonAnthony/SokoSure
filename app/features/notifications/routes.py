# app/features/notifications/routes.py

from uuid import UUID
from typing import Optional

from fastapi import APIRouter, Depends, Form, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.features.notifications.models import SMSLog
from app.features.notifications.services import NotificationService

router = APIRouter(prefix="/sms", tags=["Notifications"])

notification_service = NotificationService()


@router.post("", status_code=status.HTTP_200_OK)
async def inbound_sms(
    from_: str = Form(..., alias="from"),       # sender's phone number — always present
    text: str = Form(...),                       # message body — always present
    to: Optional[str] = Form(default=None),      # your AT shortcode — optional
    date: Optional[str] = Form(default=None),    # timestamp from AT — optional
    db: AsyncSession = Depends(get_session),
):
    """
    Africa's Talking posts here when a user sends an SMS to your shortcode.
    Drives the SMS profile-completion state machine after USSD registration.
    Also handles keyword commands: HELP, CLAIM, STATUS, MENU.
    """
    await notification_service.handle_incoming_sms(db, phone_number=from_, text=text)
    return {"received": True}


@router.get("/logs", status_code=status.HTTP_200_OK)
async def get_sms_logs(
    user_id: UUID | None = None,
    db: AsyncSession = Depends(get_session),
):
    """Retrieve SMS logs. Filter by user_id via ?user_id=<uuid>."""
    stmt = select(SMSLog).order_by(SMSLog.sent_at.desc())
    if user_id:
        stmt = stmt.where(SMSLog.user_id == user_id)

    result = await db.execute(stmt)
    return {"logs": result.scalars().all()}
