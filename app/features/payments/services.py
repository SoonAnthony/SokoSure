from datetime import datetime, timedelta, timezone
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.notifications.models import SMSDirection, SMSLog
from app.features.payments.models import PaymentStatus, PremiumPayment
from app.features.payments.schemas import PaymentInitiate, PaymentWebhookPayload
from app.features.policies.models import Policy, PolicyStatus
from app.features.users.models import PaymentFrequency


def _to_uuid(value) -> UUID:
    return value if isinstance(value, UUID) else UUID(str(value))


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


async def get_pending_policy_for_user(db: AsyncSession, user_id) -> Policy | None:
    user_uuid = _to_uuid(user_id)
    result = await db.execute(
        select(Policy).where(
            Policy.user_id == user_uuid,
            Policy.status == PolicyStatus.PENDING,
        )
    )
    return result.scalar_one_or_none()


def _calculate_expiry(from_dt: datetime, frequency: PaymentFrequency) -> datetime:
    if frequency == PaymentFrequency.DAILY:
        return from_dt + timedelta(days=1)
    if frequency == PaymentFrequency.WEEKLY:
        return from_dt + timedelta(days=7)
    return from_dt + timedelta(days=30)


async def _log_sms(db: AsyncSession, user_id, message: str) -> None:
    db.add(SMSLog(user_id=user_id, message=message, direction=SMSDirection.OUTBOUND))


# Provider client boundary 
# This is the ONLY function that needs to change once real Africa's Talking
# / M-Pesa STK Push credentials are available. Everything else in this file
# is already written correctly for the real flow.

async def _request_stk_push(policy: Policy) -> str:
    """
    Initiates an STK push / payment request with the provider and
    returns the REAL provider transaction/request reference.

    TODO: replace this stub with an actual call to Africa's Talking's
    Payments API (or M-Pesa Daraja STK Push) once credentials are set up.
    The real API call will return a checkout/request ID immediately —
    return that value here instead of the stub below.
    """
    raise NotImplementedError(
        "Africa's Talking Payments API not yet configured. "
        "See _request_stk_push() for integration point."
    )


# Public API 

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


async def initiate_premium_payment_for_user(db: AsyncSession, user_id) -> str:
    """
    Called directly by USSD when the user selects 'Pay Premium'.

    Attempts to initiate a real STK push via the provider. If the provider
    integration isn't configured yet (hackathon/demo mode), falls back to
    returning manual payment instructions without creating a PremiumPayment
    row — the row gets created later when the webhook actually arrives,
    via handle_payment_callback()'s create-or-update logic.
    """
    policy = await get_pending_policy_for_user(db, user_id)
    if not policy:
        raise ValueError("No pending policy found to pay for")

    try:
        provider_reference = await _request_stk_push(policy)

        payment = PremiumPayment(
            policy_id=policy.id,
            amount=policy.premium_amount,
            provider_transaction_id=provider_reference,
            status=PaymentStatus.PENDING,
        )
        db.add(payment)
        await db.commit()
        await db.refresh(payment)

        return "STK push sent. Enter your M-Pesa PIN to complete payment."

    except NotImplementedError:
        # Provider not yet configured — fall back to manual instructions.
        # No PremiumPayment row is created here; handle_payment_callback()
        # creates it fresh when the real payment event arrives.
        return (
            f"Pay KES {policy.premium_amount:,.0f} via M-Pesa Paybill 123456, "
            f"Account: {policy.policy_code}"
        )


async def handle_payment_callback(
    db: AsyncSession, payload: PaymentWebhookPayload
) -> tuple[PremiumPayment, bool]:
    """
    Handles the provider's payment confirmation webhook.

    Create-or-update: if a PremiumPayment already exists for this
    provider_transaction_id (real STK push flow), update it. If not
    (manual/demo flow where no row was pre-created), create it fresh.
    This makes the callback idempotent either way.
    """
    payment = await get_payment_by_provider_tx_id(db, payload.provider_transaction_id)

    if not payment:
        policy = await get_policy_by_id(db, payload.policy_id)
        if not policy:
            raise ValueError("Policy not found for incoming payment callback")

        payment = PremiumPayment(
            policy_id=payload.policy_id,
            amount=payload.amount,
            provider_transaction_id=payload.provider_transaction_id,
            status=PaymentStatus.PENDING,
        )
        db.add(payment)
        await db.flush()  # assigns payment.id without committing yet

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