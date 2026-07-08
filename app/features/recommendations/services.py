from sqlalchemy.ext.asyncio import AsyncSession

from app.features.recommendations.models import PolicyRecommendation
from app.features.recommendations.schemas import RecommendationCreate
from app.features.users.models import User


# AI Prompt Logic 

def _build_prompt(user: User) -> str:
    return (
        f"A trader in {user.county}, Kenya runs a {user.business_type} business. "
        f"Their average daily income is in the range: {user.income_bracket}. "
        f"They prefer to pay premiums {user.payment_frequency}. "
        "Recommend a micro-insurance plan with: "
        "a plan name, a premium amount in KES, a coverage amount in KES, "
        "and a short reason (1 sentence) explaining why this plan suits them."
    )


def _fallback_recommendation(user: User) -> dict:
    """
    Rule-based fallback used if the AI call fails or is not configured.
    Keeps the registration flow working even without a live AI integration.
    """
    income_to_plan = {
        "Below 500": (10, 5000),
        "500 - 1,000": (20, 15000),
        "1,000 - 3,000": (30, 30000),
        "3,000 - 10,000": (50, 60000),
        "Above 10,000": (100, 100000),
    }
    premium, coverage = income_to_plan.get(str(user.income_bracket), (30, 30000))

    return {
        "recommended_plan": "SokoSure Basic Cover",
        "premium": premium,
        "coverage": coverage,
        "reason": f"Suitable for a {user.business_type} business at this income level.",
    }


async def _call_ai(user: User) -> dict:
    """
    Calls the AI service to generate a recommendation.
    Falls back to a rule-based recommendation on any failure,
    so registration never breaks due to AI downtime.
    """
    try:
        # TODO: wire in actual AI API call here once credentials are ready.
        # prompt = _build_prompt(user)
        # response = await some_ai_client.generate(prompt)
        # parse response into plan/premium/coverage/reason
        raise NotImplementedError("AI integration not yet configured")
    except Exception:
        return _fallback_recommendation(user)


# Public API

async def create_recommendation(db: AsyncSession, user: User) -> PolicyRecommendation:
    """
    Generates a recommendation for the given user (via AI or fallback),
    stores it, and returns the saved PolicyRecommendation.
    """
    result = await _call_ai(user)

    recommendation = PolicyRecommendation(
        user_id=user.id,
        recommended_plan=result["recommended_plan"],
        premium=result["premium"],
        coverage=result["coverage"],
        reason=result["reason"],
    )

    db.add(recommendation)
    await db.commit()
    await db.refresh(recommendation)
    return recommendation


async def get_recommendation_for_user(
    db: AsyncSession, user_id
) -> PolicyRecommendation | None:
    from sqlalchemy import select
    from uuid import UUID

    user_uuid = user_id if isinstance(user_id, UUID) else UUID(str(user_id))
    result = await db.execute(
        select(PolicyRecommendation)
        .where(PolicyRecommendation.user_id == user_uuid)
        .order_by(PolicyRecommendation.created_at.desc())
    )
    return result.scalars().first()