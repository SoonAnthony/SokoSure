from random import randint
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.claims.models import Claim, ClaimStatus
from app.features.claims.schemas import ClaimCreate
from app.features.policies.models import Policy, PolicyStatus
from app.features.notifications.services import NotificationService

notification_service = NotificationService()


def _generate_claim_code() -> str:
    return f"CL{randint(100000, 999999)}"


def _to_uuid(value) -> UUID:
    return value if isinstance(value, UUID) else UUID(str(value))


async def get_claim_by_id(db: AsyncSession, claim_id):
    result = await db.execute(select(Claim).where(Claim.id == claim_id))
    return result.scalar_one_or_none()


async def get_policy_by_id(db: AsyncSession, policy_id):
    result = await db.execute(select(Policy).where(Policy.id == policy_id))
    return result.scalar_one_or_none()


async def get_claims_by_user_id(db: AsyncSession, user_id):
    stmt = (
        select(Claim)
        .join(Policy, Claim.policy_id == Policy.id)
        .where(Policy.user_id == user_id)
        .order_by(Claim.filed_at.desc())
    )
    result = await db.execute(stmt)
    return result.scalars().all()


async def submit_claim(db: AsyncSession, payload: ClaimCreate) -> Claim:
    policy = await get_policy_by_id(db, payload.policy_id)
    if not policy:
        raise ValueError("Policy not found")

    if policy.status != PolicyStatus.ACTIVE:
        raise ValueError("Only active policies can file claims")

    duplicate_stmt = select(Claim).where(
        Claim.policy_id == payload.policy_id,
        Claim.category == payload.category,
        Claim.description == payload.description,
        Claim.status.in_([ClaimStatus.SUBMITTED, ClaimStatus.UNDER_REVIEW]),
    )
    duplicate_result = await db.execute(duplicate_stmt)
    duplicate_claim = duplicate_result.scalar_one_or_none()
    if duplicate_claim:
        raise ValueError("A similar pending claim already exists")

    claim = Claim(
        policy_id=payload.policy_id,
        category=payload.category,
        description=payload.description,
        claim_code=_generate_claim_code(),
        status=ClaimStatus.SUBMITTED,
    )
    db.add(claim)
    await db.commit()
    await db.refresh(claim)

    # Send real SMS via Notification Service, instead of writing SMSLog directly
    await notification_service.send_claim_confirmation_sms(db, policy.user_id, claim)

    return claim


async def submit_claim_for_user(
    db: AsyncSession,
    user_id,
    category: str,
    description: str,
) -> Claim:
    """
    Called directly by USSD. Looks up the user's active policy,
    then delegates to submit_claim().
    """
    user_uuid = _to_uuid(user_id)

    result = await db.execute(
        select(Policy).where(
            Policy.user_id == user_uuid,
            Policy.status == PolicyStatus.ACTIVE,
        )
    )
    policy = result.scalar_one_or_none()
    if not policy:
        raise ValueError("No active policy found for this user")

    payload = ClaimCreate(
        policy_id=policy.id,
        category=category,
        description=description,
    )
    return await submit_claim(db, payload)


async def update_claim_status(db: AsyncSession, claim_id, status: ClaimStatus) -> Claim | None:
    claim = await get_claim_by_id(db, claim_id)
    if not claim:
        return None

    claim.status = status
    db.add(claim)
    await db.commit()
    await db.refresh(claim)
    return claim