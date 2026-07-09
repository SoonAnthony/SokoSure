import logging

import africastalking
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.features.notifications.models import SMSDirection, SMSLog, SMSSession, SMSSessionState
from app.features.users.models import User
from app.features.ussd.constants import COUNTIES, BUSINESS_OPTIONS, INCOME_OPTIONS, FREQUENCY_OPTIONS

logger = logging.getLogger(__name__)

# Lazy-initialise the AT SDK so it doesn't fail at import time if credentials
# aren't set yet (e.g. during testing or first boot).
_sms_client = None

def _sms():
    global _sms_client
    if _sms_client is None:
        africastalking.initialize(settings.AT_USERNAME, settings.AT_API_KEY)
        _sms_client = africastalking.SMS
    return _sms_client


class NotificationService:
    """
    Central SMS gateway for the entire application.
    Handles both outbound notifications and the inbound SMS profile-completion
    conversation triggered after USSD registration.
    """

    # ─── Core ─────────────────────────────────────────────────────────────────

    async def send_sms(self, db: AsyncSession, user: User, message: str) -> dict | None:
        """
        Send an SMS to a User object and log it.

        Never raises — SMS delivery failures (bad credentials, AT sandbox
        flakiness, network issues) must not break the calling flow
        (registration, claims, payments). On failure, we log the error and
        still record the attempted message so support/debugging can see it.
        """
        try:
            response = _sms().send(message, [user.phone_no], sender_id=settings.AT_SHORTCODE)
        except Exception:
            logger.exception("Failed to send SMS to user")
            response = None

        await self._log(db, user.id, message, SMSDirection.OUTBOUND)
        return response

    async def send_sms_to_phone(self, phone_number: str, message: str) -> dict | None:
        """
        Send an SMS to a raw phone number (no DB log — caller logs if needed).
        Never raises, for the same reason as send_sms().
        """
        try:
            return _sms().send(message, [phone_number], sender_id=settings.AT_SHORTCODE)
        except Exception:
            logger.exception("Failed to send SMS to phone number")
            return None

    async def _log(
        self, db: AsyncSession, user_id, message: str, direction: SMSDirection
    ) -> None:
        db.add(SMSLog(user_id=user_id, message=message, direction=direction))
        await db.commit()

    # ─── Welcome SMS (triggers profile completion flow) ───────────────────────

    async def send_welcome_sms(self, db: AsyncSession, user: User) -> None:
        """
        Sent right after USSD registration.
        Creates an SMSSession so the user's replies are tracked,
        then asks for their full name to start the profile flow.
        """
        # Create the SMS session for this user
        sms_session = SMSSession(
            phone_number=user.phone_no,
            state=SMSSessionState.AWAIT_NAME,
        )
        db.add(sms_session)
        await db.commit()

        await self.send_sms(
            db, user,
            "Welcome to SokoSure!\n"
            "Let's complete your profile.\n"
            "Reply with your Full Name:",
        )

    # ─── Inbound SMS Handler (state machine) ──────────────────────────────────

    async def handle_incoming_sms(
        self, db: AsyncSession, phone_number: str, text: str
    ) -> None:
        """
        Entry point for all inbound SMS messages.
        If the user has an active SMSSession (profile not yet complete),
        advance the profile-completion state machine.
        Otherwise handle as a keyword command.
        """
        text = text.strip()

        # Look up user
        result = await db.execute(select(User).where(User.phone_no == phone_number))
        user = result.scalar_one_or_none()

        if user:
            await self._log(db, user.id, text, SMSDirection.INBOUND)

        # Check for an active profile-completion session
        session_result = await db.execute(
            select(SMSSession).where(SMSSession.phone_number == phone_number)
        )
        sms_session = session_result.scalar_one_or_none()

        if sms_session and sms_session.state != SMSSessionState.COMPLETE:
            await self._advance_profile(db, user, sms_session, text)
            return

        # No active session — handle as keyword command
        await self._handle_keyword(db, user, phone_number, text)

    async def _advance_profile(
        self,
        db: AsyncSession,
        user: User,
        session: SMSSession,
        text: str,
    ) -> None:
        """
        Walk the user through profile completion one reply at a time.
        Each state collects one field, validates it, saves it, and
        asks for the next field.
        """
        state = session.state

        if state == SMSSessionState.AWAIT_NAME:
            if len(text) < 2:
                await self.send_sms_to_phone(
                    user.phone_no, "Please enter your full name:"
                )
                return
            session.full_name = text
            session.state = SMSSessionState.AWAIT_COUNTY
            db.add(session)
            await db.commit()
            await self.send_sms_to_phone(
                user.phone_no,
                "Enter your County\n(e.g. NAIROBI, MOMBASA, KISUMU):",
            )

        elif state == SMSSessionState.AWAIT_COUNTY:
            county = text.upper().replace(" ", "_")
            if county not in COUNTIES:
                await self.send_sms_to_phone(
                    user.phone_no,
                    "County not recognised. Try again\n(e.g. NAIROBI, MOMBASA, KISUMU):",
                )
                return
            session.county = county
            session.state = SMSSessionState.AWAIT_BUSINESS
            db.add(session)
            await db.commit()
            await self.send_sms_to_phone(
                user.phone_no,
                "Select Business Type. Reply with number:\n"
                "1. Mama Mboga\n2. Mitumba\n3. Kibanda Food\n"
                "4. Salon/Barbershop\n5. Jua Kali\n6. Electronics\n"
                "7. Shoes & Bags\n8. Duka\n9. Tailoring\n0. Other",
            )

        elif state == SMSSessionState.AWAIT_BUSINESS:
            if text not in BUSINESS_OPTIONS:
                await self.send_sms_to_phone(
                    user.phone_no, "Invalid option. Reply with a number (0-9):"
                )
                return
            session.business = BUSINESS_OPTIONS[text]
            session.state = SMSSessionState.AWAIT_INCOME
            db.add(session)
            await db.commit()
            await self.send_sms_to_phone(
                user.phone_no,
                "Average Daily Income. Reply with number:\n"
                "1. Below 500\n2. 500-1,000\n"
                "3. 1,000-3,000\n4. 3,000-10,000\n5. Above 10,000",
            )

        elif state == SMSSessionState.AWAIT_INCOME:
            if text not in INCOME_OPTIONS:
                await self.send_sms_to_phone(
                    user.phone_no, "Invalid option. Reply with a number (1-5):"
                )
                return
            session.income = INCOME_OPTIONS[text]
            session.state = SMSSessionState.AWAIT_FREQUENCY
            db.add(session)
            await db.commit()
            await self.send_sms_to_phone(
                user.phone_no,
                "Payment Frequency. Reply with number:\n"
                "1. Daily\n2. Weekly\n3. Monthly",
            )

        elif state == SMSSessionState.AWAIT_FREQUENCY:
            if text not in FREQUENCY_OPTIONS:
                await self.send_sms_to_phone(
                    user.phone_no, "Invalid option. Reply 1, 2, or 3:"
                )
                return

            frequency = FREQUENCY_OPTIONS[text]

            # All data collected — update the user's profile
            from app.features.users.schemas import UserCompleteProfile
            from app.features.users import services as user_services

            await user_services.complete_profile(
                db,
                user.id,
                UserCompleteProfile(
                    full_name=session.full_name,
                    county=session.county,
                    business_type=session.business,
                    income_bracket=session.income,
                    payment_frequency=frequency,
                ),
            )

            # Mark session complete
            session.state = SMSSessionState.COMPLETE
            db.add(session)
            await db.commit()

            await self.send_sms(
                db, user,
                "Profile complete!\n"
                "We are preparing your insurance recommendation.\n"
                "You will receive it shortly.",
            )

    async def _handle_keyword(
        self, db: AsyncSession, user: User | None, phone_number: str, text: str
    ) -> None:
        """Handle keyword commands for users who have already completed their profile."""
        keyword = text.upper()
        replies = {
            "HELP":   "SokoSure Support\nCall: 0800 720 000\nDial *384# to manage your policy.",
            "CLAIM":  "To file a claim, dial *384# and select File Claim.",
            "STATUS": "Dial *384# and select View Policy to check your status.",
            "MENU":   "Dial *384# to access your SokoSure dashboard.",
        }
        reply = replies.get(keyword, "Reply HELP for assistance or dial *384#.")
        await self.send_sms_to_phone(phone_number, reply)
        if user:
            await self._log(db, user.id, reply, SMSDirection.OUTBOUND)

    # ─── Event-Specific Outbound SMS ──────────────────────────────────────────

    async def send_recommendation_sms(
        self, db: AsyncSession, user: User, plan: str, premium: float, coverage: float
    ) -> None:
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
        await self.send_sms(
            db, user,
            f"Payment received.\nPolicy Active.\nCoverage: KES {coverage:,.0f}.",
        )

    async def send_claim_confirmation(
        self, db: AsyncSession, user: User, claim_code: str
    ) -> None:
        await self.send_sms(
            db, user,
            f"Claim received.\nReference: {claim_code}.\nWe will review it shortly.",
        )