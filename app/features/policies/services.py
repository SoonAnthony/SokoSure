from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import random
import string

from app.features.policies.models import Policy, PolicyStatus
from app.features.users.models import User, PaymentFrequency
from app.features.recommendations import services as recommendation_services


def _to_uuid(value) -> UUID:
    return value if isinstance(value, UUID) else UUID(str(value))


def _generate_policy_code() -> str:
    suffix = "".join(random.choices(string.digits, k=5))
    return f"SK{suffix}"


async def _unique_policy_code(db: AsyncSession) -> str:
    for _ in range(5):
        code = _generate_policy_code()
        result = await db.execute(select(Policy).where(Policy.policy_code == code))
        if not result.scalar_one_or_none():
            return code
    raise ValueError("Could not generate a unique policy code")


# Public API 

async def create_policy(
    db: AsyncSession,
    user_id: UUID,
    recommendation_id: UUID,
    coverage_amount: float,
    premium_amount: float,
    premium_frequency: PaymentFrequency,
) -> Policy:
    policy_code = await _unique_policy_code(db)

    policy = Policy(
        user_id=user_id,
        recommendation_id=recommendation_id,
        policy_code=policy_code,
        status=PolicyStatus.PENDING,
        coverage_amount=coverage_amount,
        premium_amount=premium_amount,
        premium_frequency=premium_frequency,
    )

    db.add(policy)
    await db.commit()
    await db.refresh(policy)
    return policy


async def generate_recommendation(db: AsyncSession, user: User) -> Policy:
    """
    Called directly by USSD right after registration.
    Orchestrates: AI recommendation -> store recommendation -> create PENDING policy.
    """
    recommendation = await recommendation_services.create_recommendation(db, user)

    policy = await create_policy(
        db,
        user_id=user.id,
        recommendation_id=recommendation.id,
        coverage_amount=recommendation.coverage,
        premium_amount=recommendation.premium,
        premium_frequency=user.payment_frequency,
    )
    return policy


async def get_active_policy_for_user(db: AsyncSession, user_id) -> Policy | None:
    user_uuid = _to_uuid(user_id)
    result = await db.execute(
        select(Policy).where(
            Policy.user_id == user_uuid,
            Policy.status == PolicyStatus.ACTIVE,
        )
    )
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


async def get_activation_instructions(db: AsyncSession, user_id) -> str | None:
    """
    Called directly by USSD when the user selects 'Activate Policy'.
    Returns instructions text, or None if there's no pending policy.
    """
    policy = await get_pending_policy_for_user(db, user_id)
    if not policy:
        return None

    return (
        f"Policy: {policy.policy_code}\n"
        f"Premium: KES {policy.premium_amount:,.0f} ({policy.premium_frequency})\n"
        "Pay via M-Pesa Paybill 123456 to activate."
    )


async def activate_policy(db: AsyncSession, policy_id: UUID) -> Policy | None:
    """
    Called by Payments (Member 3) after a successful payment callback.
    """
    from datetime import datetime, timedelta, timezone

    result = await db.execute(select(Policy).where(Policy.id == policy_id))
    policy = result.scalar_one_or_none()
    if not policy:
        return None

    frequency_days = {"Daily": 1, "Weekly": 7, "Monthly": 30}
    days = frequency_days.get(str(policy.premium_frequency), 30)

    policy.status = PolicyStatus.ACTIVE
    policy.activated_at = datetime.now(timezone.utc)
    policy.expires_at = datetime.now(timezone.utc) + timedelta(days=days)

    db.add(policy)
    await db.commit()
    await db.refresh(policy)
    return policy