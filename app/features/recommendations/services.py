# app/features/recommendations/services.py

import json
from google import genai
from google.genai import types
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.features.recommendations.models import PolicyRecommendation
from app.features.users.models import User

# Lazy-init Gemini client
_gemini_client = None

def _model():
    global _gemini_client
    if _gemini_client is None:
        _gemini_client = genai.Client(api_key=settings.GEMINI_API_KEY)
    return _gemini_client


# ─── Prompt ───────────────────────────────────────────────────────────────────

def _build_prompt(user: User) -> str:
    return (
        f"A trader in {user.county}, Kenya runs a {user.business_type} business. "
        f"Their average daily income is: {user.income_bracket} KES. "
        f"They prefer to pay premiums {user.payment_frequency}. "
        "Recommend a micro-insurance plan for them. "
        "Respond ONLY with a valid JSON object with exactly these keys: "
        "\"recommended_plan\" (string, short plan name), "
        "\"premium\" (number, amount in KES per payment period), "
        "\"coverage\" (number, total coverage amount in KES), "
        "\"reason\" (string, one sentence explaining why this plan suits them). "
        "Do not include any text outside the JSON object."
    )


# ─── Fallback ─────────────────────────────────────────────────────────────────

def _fallback_recommendation(user: User) -> dict:
    """Rule-based fallback if Gemini fails or is unavailable."""
    income_to_plan = {
        "Below 500":       (10,  5_000),
        "500 - 1,000":     (20,  15_000),
        "1,000 - 3,000":   (30,  30_000),
        "3,000 - 10,000":  (50,  60_000),
        "Above 10,000":    (100, 100_000),
    }
    premium, coverage = income_to_plan.get(str(user.income_bracket), (30, 30_000))
    return {
        "recommended_plan": "SokoSure Basic Cover",
        "premium": premium,
        "coverage": coverage,
        "reason": f"Suitable for a {user.business_type} business at this income level.",
    }


# ─── Gemini Call ──────────────────────────────────────────────────────────────

async def _call_gemini(user: User) -> dict:
    """
    Calls Gemini to generate a personalised recommendation.
    Falls back to rule-based logic on any failure so the flow never breaks.
    """
    try:
        prompt = _build_prompt(user)
        response = _model().models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )

        # Strip markdown code fences if Gemini wraps the JSON in ```json ... ```
        raw = response.text.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()

        data = json.loads(raw)

        # Validate required keys are present
        required = {"recommended_plan", "premium", "coverage", "reason"}
        if not required.issubset(data.keys()):
            raise ValueError("Gemini response missing required keys")

        return {
            "recommended_plan": str(data["recommended_plan"]),
            "premium": float(data["premium"]),
            "coverage": float(data["coverage"]),
            "reason": str(data["reason"]),
        }

    except Exception:
        return _fallback_recommendation(user)


# ─── Public API ───────────────────────────────────────────────────────────────

async def create_recommendation(db: AsyncSession, user: User) -> PolicyRecommendation:
    """
    Generates a recommendation via Gemini (or fallback),
    stores it, and returns the saved PolicyRecommendation.
    """
    result = await _call_gemini(user)

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
