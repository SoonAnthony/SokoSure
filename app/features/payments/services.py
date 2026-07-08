from datetime import datetime, timedelta, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.notifications.models import SMSDirection, SMSLog
from app.features.payments.models import PaymentStatus, PremiumPayment
from app.features.payments.schemas import PaymentInitiate, PaymentWebhookPayload
from app.features.policies.models import Policy, PolicyStatus
from app.features.users.models import PaymentFrequency


async def get_payment_by_id(db: AsyncSession, payment_id):
    result = await db.execute(select(PremiumPayment).where(PremiumPayment.id == payment_id))
    return result.scalar_one_or_none()


async def get_payment_by_provider_tx_id(db: AsyncSession, provider_transaction_id: str):
    result = await db.execute(
        select(PremiumPayment).where(
            PremiumPayment.provider_transaction_id == provider_transaction_id
        )
    )
    return result.scalar_one_or_none()


async def get_policy_by_id(db: AsyncSession, policy_id):
    result = await db.execute(select(Policy).where(Policy.id == policy_id))
    return result.scalar_one_or_none()


def _calculate_expiry(from_dt: datetime, frequency: PaymentFrequency) -> datetime:
    if frequency == PaymentFrequency.DAILY:
        return from_dt + timedelta(days=1)
    if frequency == PaymentFrequency.WEEKLY:
        return from_dt + timedelta(days=7)
    return from_dt + timedelta(days=30)


async def _log_sms(db: AsyncSession, user_id, message: str) -> None:
    db.add(SMSLog(user_id=user_id, message=message, direction=SMSDirection.OUTBOUND))


async def initiate_payment(db: AsyncSession, payload: PaymentInitiate) -> PremiumPayment:
    policy = await get_policy_by_id(db, payload.policy_id)
    if not policy:
        raise ValueError("Policy not found")

    existing = await get_payment_by_provider_tx_id(db, payload.provider_transaction_id)
    if existing:
        raise ValueError("provider_transaction_id already exists")

    payment = PremiumPayment(
        policy_id=payload.policy_id,
        amount=payload.amount,
        provider_transaction_id=payload.provider_transaction_id,
        status=PaymentStatus.PENDING,
    )
    db.add(payment)
    await db.commit()
    await db.refresh(payment)
    return payment


async def handle_payment_callback(
    db: AsyncSession, payload: PaymentWebhookPayload
) -> tuple[PremiumPayment, bool]:
    payment = await get_payment_by_provider_tx_id(db, payload.provider_transaction_id)
    if not payment:
        raise ValueError("Payment not found for provider transaction")

    if payment.policy_id != payload.policy_id:
        raise ValueError("policy_id mismatch for provider transaction")

    payment.amount = payload.amount
    payment.status = payload.status

    policy_activated = False
    if payload.status == PaymentStatus.CONFIRMED:
        payment.paid_at = datetime.now(timezone.utc).replace(tzinfo=None)
        policy = await get_policy_by_id(db, payload.policy_id)
        if policy and policy.status != PolicyStatus.ACTIVE:
            activated_at = datetime.now(timezone.utc).replace(tzinfo=None)
            policy.status = PolicyStatus.ACTIVE
            policy.activated_at = activated_at
            policy.expires_at = _calculate_expiry(activated_at, policy.premium_frequency)
            policy_activated = True
            await _log_sms(
                db,
                policy.user_id,
                f"Payment confirmed. Policy {policy.policy_code} is now active.",
            )

    if payload.status == PaymentStatus.FAILED:
        policy = await get_policy_by_id(db, payload.policy_id)
        if policy:
            await _log_sms(
                db,
                policy.user_id,
                f"Payment failed for policy {policy.policy_code}. Please retry.",
            )

    db.add(payment)
    await db.commit()
    await db.refresh(payment)
    return payment, policy_activated
