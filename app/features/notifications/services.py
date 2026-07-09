# app/features/notifications/services.py

import africastalking
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.features.notifications.models import SMSDirection, SMSLog
from app.features.users.models import User

# Lazy-initialise the AT SDK so it doesn't fail at import time if credentials
# aren't set yet (e.g. during testing or first boot).
_sms_client = None

def _sms():
    global _sms_client
    if _sms_client is None:
        africastalking.initialize(settings.AT_USERNAME, settings.AT_API_KEY)
        _sms_client = africastalking.SMS
    return _sms_client


# Keyword → auto-reply map for inbound SMS handling
_KEYWORDS: dict[str, str] = {
    "YES":    "Your request has been received. We will process it shortly.",
    "HELP":   "SokoSure Support\nCall: 0800 720 000\nDial *384# to manage your policy.",
    "CLAIM":  "To file a claim, dial *384# and select File Claim from your dashboard.",
    "STATUS": "Dial *384# and select View Policy to check your policy status.",
    "MENU":   "Dial *384# to access your SokoSure dashboard.",
}


class NotificationService:
    """
    Central SMS gateway for the entire application.
    No other feature should call Africa's Talking directly.
    Every outbound SMS is sent here and logged to the database.
    """

    # ─── Core ─────────────────────────────────────────────────────────────────

    async def send_sms(self, db: AsyncSession, user: User, message: str) -> dict:
        """Send an SMS to a User object and log it."""
        response = _sms().send(message, [user.phone_no])
        await self._log(db, user.id, message, SMSDirection.OUTBOUND)
        return response

    async def send_sms_to_phone(self, phone_number: str, message: str) -> dict:
        """Send an SMS to a raw phone number (no DB log — caller logs if needed)."""
        return _sms().send(message, [phone_number])

    async def _log(
        self, db: AsyncSession, user_id, message: str, direction: SMSDirection
    ) -> None:
        """Persist an SMS record."""
        db.add(SMSLog(user_id=user_id, message=message, direction=direction))
        await db.commit()

    # ─── Inbound SMS Handler ──────────────────────────────────────────────────

    async def handle_incoming_sms(
        self, db: AsyncSession, phone_number: str, text: str
    ) -> None:
        """
        Called by POST /sms when Africa's Talking delivers an inbound message.
        Logs the inbound message, then replies based on the keyword.
        Unrecognised keywords fall back to the HELP reply.
        """
        keyword = text.strip().upper()

        # Look up user to log against their id
        result = await db.execute(select(User).where(User.phone_no == phone_number))
        user = result.scalar_one_or_none()

        if user:
            await self._log(db, user.id, text, SMSDirection.INBOUND)

        reply = _KEYWORDS.get(keyword, _KEYWORDS["HELP"])
        await self.send_sms_to_phone(phone_number, reply)

        if user:
            await self._log(db, user.id, reply, SMSDirection.OUTBOUND)

    # ─── Event-Specific Outbound SMS ──────────────────────────────────────────

    async def send_welcome_sms(self, db: AsyncSession, user: User) -> None:
        """Sent immediately after USSD registration."""
        await self.send_sms(
            db, user,
            "Welcome to SokoSure!\n"
            "Your account has been created.\n"
            "Reply MENU to get started or dial *384#.",
        )

    async def send_recommendation_sms(
        self, db: AsyncSession, user: User, plan: str, premium: float, coverage: float
    ) -> None:
        """Sent when a recommendation is ready."""
        await self.send_sms(
            db, user,
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
            db, user,
            f"Payment received.\nPolicy Active.\nCoverage: KES {coverage:,.0f}.",
        )

    async def send_claim_confirmation(
        self, db: AsyncSession, user: User, claim_code: str
    ) -> None:
        """Sent when a claim is submitted."""
        await self.send_sms(
            db, user,
            f"Claim received.\nReference: {claim_code}.\nWe will review it shortly.",
        )
