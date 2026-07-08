from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.features.payments.schemas import PaymentInitiate, PaymentRead, PaymentWebhookPayload
from app.features.payments import services as payment_services

router = APIRouter()


@router.post("/initiate", response_model=PaymentRead, status_code=status.HTTP_201_CREATED)
async def initiate_payment(
    payload: PaymentInitiate, db: AsyncSession = Depends(get_session)
):
    try:
        payment = await payment_services.initiate_payment(db, payload)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return payment


@router.post("/callback")
async def payment_callback(
    payload: PaymentWebhookPayload, db: AsyncSession = Depends(get_session)
):
    try:
        payment, policy_activated = await payment_services.handle_payment_callback(
            db, payload
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return {
        "payment_id": str(payment.id),
        "status": payment.status,
        "policy_activated": policy_activated,
    }


@router.get("/{payment_id}", response_model=PaymentRead)
async def get_payment(payment_id: UUID, db: AsyncSession = Depends(get_session)):
    payment = await payment_services.get_payment_by_id(db, payment_id)
    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")
    return payment
