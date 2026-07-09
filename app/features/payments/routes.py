# app/features/payments/routes.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.features.payments.schemas import PaymentWebhookPayload
from app.features.payments import services as payment_services

router = APIRouter()


# Only exposed if the payment provider sends async server-to-server confirmations.
# For the hackathon MVP, payment is simulated inside USSD → PaymentService directly.
@router.post("/callback")
async def payment_callback(
    payload: PaymentWebhookPayload, db: AsyncSession = Depends(get_session)
):
    """
    Receives payment confirmation from Africa's Talking Payments / M-Pesa.
    Activates the policy and sends an SMS confirmation on success.
    """
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
