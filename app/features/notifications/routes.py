# app/features/notifications/routes.py

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.features.notifications.models import SMSLog
from app.features.notifications.schemas import SMSSend
from app.features.notifications.services import NotificationService
from app.features.users import services as user_services

router = APIRouter(prefix="/sms", tags=["Notifications"])

notification_service = NotificationService()


@router.post("/send", status_code=status.HTTP_200_OK)
async def send_sms(payload: SMSSend, db: AsyncSession = Depends(get_session)):
    """Send an SMS to a user by user_id. All SMS must go through this endpoint."""
    user = await user_services.get_user_by_id(db, payload.user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    try:
        response = await notification_service.send_sms(db, user, payload.message)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))

    return {"status": "sent", "at_response": response}


@router.get("/logs", status_code=status.HTTP_200_OK)
async def get_sms_logs(
    user_id: UUID | None = None,
    db: AsyncSession = Depends(get_session),
):
    """
    Retrieve SMS logs.
    Optionally filter by user_id via query param: /sms/logs?user_id=<uuid>
    """
    stmt = select(SMSLog).order_by(SMSLog.sent_at.desc())
    if user_id:
        stmt = stmt.where(SMSLog.user_id == user_id)

    result = await db.execute(stmt)
    logs = result.scalars().all()
    return {"logs": logs}
