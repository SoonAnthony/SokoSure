from random import randint
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.claims.models import Claim, ClaimStatus
from app.features.claims.schemas import ClaimCreate
from app.features.notifications.models import SMSDirection, SMSLog
from app.features.policies.models import Policy, PolicyStatus


def _generate_claim_code() -> str:
    return f"CL{randint(100000, 999999)}"


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


async def _log_sms(db: AsyncSession, user_id, message: str) -> None:
    db.add(SMSLog(user_id=user_id, message=message, direction=SMSDirection.OUTBOUND))


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
    await _log_sms(
        db,
        policy.user_id,
        f"Claim {claim.claim_code} received for policy {policy.policy_code}.",
    )
    await db.commit()
    await db.refresh(claim)
    return claim


async def update_claim_status(db: AsyncSession, claim_id, status: ClaimStatus) -> Claim | None:
    claim = await get_claim_by_id(db, claim_id)
    if not claim:
        return None

    claim.status = status
    db.add(claim)
    await db.commit()
    await db.refresh(claim)
    return claim
