# app/features/notifications/services.py

import africastalking
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.features.notifications.models import SMSDirection, SMSLog
from app.features.users.models import User

# Initialise Africa's Talking SDK once at import time
africastalking.initialize(settings.AT_USERNAME, settings.AT_API_KEY)
_sms = africastalking.SMS


class NotificationService:
    """
    Central SMS gateway for the entire application.
    No other feature should call Africa's Talking directly.
    Every outbound SMS is sent here and logged to the database.
    """

    # ─── Core Methods ─────────────────────────────────────────────────────────

    async def send_sms(
        self, db: AsyncSession, user: User, message: str
    ) -> dict:
        """
        Send an SMS via Africa's Talking and log it.
        Returns the AT API response dict.
        Raises on send failure so callers can handle it.
        """
        response = _sms.send(message, [user.phone_no])
        await self.log_sms(db, user.id, message)
        return response

    async def log_sms(
        self, db: AsyncSession, user_id, message: str
    ) -> None:
        """Persist an outbound SMS record to the database."""
        db.add(
            SMSLog(
                user_id=user_id,
                message=message,
                direction=SMSDirection.OUTBOUND,
            )
        )
        await db.commit()

    # ─── Event-Specific SMS Methods ───────────────────────────────────────────

    async def send_welcome_sms(self, db: AsyncSession, user: User) -> None:
        """Sent immediately after a user completes registration."""
        await self.send_sms(
            db,
            user,
            "Welcome to SokoSure!\n"
            "Your account has been created.\n"
            "We are preparing your insurance recommendation.",
        )

    async def send_recommendation_sms(
        self,
        db: AsyncSession,
        user: User,
        plan: str,
        premium: float,
        coverage: float,
    ) -> None:
        """Sent when the Recommendation Service has generated a plan."""
        await self.send_sms(
            db,
            user,
            f"Recommended Plan: {plan}\n"
            f"Premium: KES {premium:,.0f}/week\n"
            f"Coverage: KES {coverage:,.0f}\n"
            "Reply YES to activate.",
        )

    async def send_payment_confirmation(
        self, db: AsyncSession, user: User, coverage: float
    ) -> None:
        """Sent when a premium payment is confirmed."""
        await self.send_sms(
            db,
            user,
            f"Payment received.\n"
            f"Policy Active.\n"
            f"Coverage: KES {coverage:,.0f}.",
        )

    async def send_claim_confirmation(
        self, db: AsyncSession, user: User, claim_code: str
    ) -> None:
        """Sent when a claim is successfully submitted."""
        await self.send_sms(
            db,
            user,
            f"Claim received.\n"
            f"Reference: {claim_code}.\n"
            "We will review it shortly.",
        )
