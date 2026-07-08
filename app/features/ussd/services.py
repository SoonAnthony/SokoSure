# app/features/ussd/services.py

from fastapi.responses import PlainTextResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.ussd.constants import (
    USSDState,
    COUNTIES,
    BUSINESS_OPTIONS,
    INCOME_OPTIONS,
    FREQUENCY_OPTIONS,
    CLAIM_CATEGORY_OPTIONS,
)
from app.features.ussd.models import USSDSession
from app.features.users.schemas import UserCreate
from app.features.users import services as user_services
from app.features.policies import services as policy_services
from app.features.payments import services as payment_services
from app.features.claims import services as claim_services
from app.features.notifications.services import NotificationService

notification_service = NotificationService()


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _con(text: str) -> PlainTextResponse:
    """Return a CON response (session continues)."""
    return PlainTextResponse(f"CON {text}", media_type="text/plain")


def _end(text: str) -> PlainTextResponse:
    """Return an END response (session terminates)."""
    return PlainTextResponse(f"END {text}", media_type="text/plain")


def _invalid() -> PlainTextResponse:
    """Standard invalid-input prompt that keeps the session alive."""
    return _con("Invalid input.\nTry again.")


async def _get_or_create_session(
    db: AsyncSession, session_id: str, phone_number: str
) -> USSDSession:
    """Retrieve an existing session or create a fresh one."""
    result = await db.execute(
        select(USSDSession).where(USSDSession.session_id == session_id)
    )
    session = result.scalar_one_or_none()
    if not session:
        session = USSDSession(session_id=session_id, phone_number=phone_number)
        db.add(session)
        await db.commit()
        await db.refresh(session)
    return session


async def _save(db: AsyncSession, session: USSDSession) -> None:
    """Persist session state changes."""
    db.add(session)
    await db.commit()


# ─── Main Entry Point ─────────────────────────────────────────────────────────

class USSDService:

    async def handle_request(
        self,
        db: AsyncSession,
        session_id: str,
        phone_number: str,
        text: str,
    ) -> PlainTextResponse:
        """
        Entry point called by the route.
        Restores session, extracts the latest user input, and dispatches
        to the correct state handler.
        """
        session = await _get_or_create_session(db, session_id, phone_number)

        # Africa's Talking sends the full input chain separated by '*'.
        # We only need the last value the user just typed.
        parts = text.split("*") if text else []
        user_input = parts[-1] if parts else ""

        # First request (empty text) always shows the main menu
        if not text:
            session.state = USSDState.MAIN_MENU
            await _save(db, session)
            return self.show_main_menu()

        # Dispatch to the handler for the current state
        return await self._dispatch(db, session, user_input)

    async def _dispatch(
        self, db: AsyncSession, session: USSDSession, user_input: str
    ) -> PlainTextResponse:
        """Route to the correct handler based on the session's current state."""
        state = session.state

        if state == USSDState.MAIN_MENU:
            return await self.handle_main_menu(db, session, user_input)

        # Registration flow
        if state == USSDState.REGISTER_ID:
            return await self.handle_register_id(db, session, user_input)
        if state == USSDState.REGISTER_NAME:
            return await self.handle_register_name(db, session, user_input)
        if state == USSDState.REGISTER_PIN:
            return await self.handle_register_pin(db, session, user_input)
        if state == USSDState.REGISTER_CONFIRM:
            return await self.handle_register_confirm(db, session, user_input)
        if state == USSDState.REGISTER_COUNTY:
            return await self.handle_register_county(db, session, user_input)
        if state == USSDState.REGISTER_BUSINESS:
            return await self.handle_register_business(db, session, user_input)
        if state == USSDState.REGISTER_INCOME:
            return await self.handle_register_income(db, session, user_input)
        if state == USSDState.REGISTER_FREQUENCY:
            return await self.handle_register_frequency(db, session, user_input)

        # Login flow
        if state == USSDState.LOGIN_ID:
            return await self.handle_login_id(db, session, user_input)
        if state == USSDState.LOGIN_PIN:
            return await self.handle_login_pin(db, session, user_input)

        # Dashboard and sub-flows
        if state == USSDState.DASHBOARD:
            return await self.handle_dashboard(db, session, user_input)
        if state == USSDState.VIEW_POLICY:
            return await self.handle_view_policy(db, session, user_input)
        if state == USSDState.ACTIVATE_POLICY:
            return await self.handle_activate_policy(db, session, user_input)
        if state == USSDState.PAY_PREMIUM:
            return await self.handle_pay_premium(db, session, user_input)
        if state == USSDState.FILE_CLAIM_TYPE:
            return await self.handle_file_claim_type(db, session, user_input)
        if state == USSDState.FILE_CLAIM_DESC:
            return await self.handle_file_claim_desc(db, session, user_input)
        if state == USSDState.HELP:
            return await self.handle_help(db, session, user_input)

        # Fallback — should never reach here in normal flow
        return _end("Session error. Please dial again.")

    # ─── Menus ────────────────────────────────────────────────────────────────

    def show_main_menu(self) -> PlainTextResponse:
        return _con(
            "Welcome to SokoSure\n"
            "1. Register\n"
            "2. Login"
        )

    def show_dashboard(self) -> PlainTextResponse:
        return _con(
            "Dashboard\n"
            "1. View Policy\n"
            "2. Activate Policy\n"
            "3. Pay Premium\n"
            "4. File Claim\n"
            "5. Help\n"
            "6. Logout"
        )

    # ─── Main Menu Handler ────────────────────────────────────────────────────

    async def handle_main_menu(
        self, db: AsyncSession, session: USSDSession, user_input: str
    ) -> PlainTextResponse:
        if user_input == "1":
            session.state = USSDState.REGISTER_ID
            await _save(db, session)
            return _con("Enter your National ID")

        if user_input == "2":
            session.state = USSDState.LOGIN_ID
            await _save(db, session)
            return _con("Enter your National ID")

        return _invalid()

    # ─── Registration Handlers ────────────────────────────────────────────────

    async def handle_register_id(
        self, db: AsyncSession, session: USSDSession, user_input: str
    ) -> PlainTextResponse:
        """Validate that National ID contains digits only."""
        if not user_input.isdigit():
            return _invalid()

        session.national_id = user_input
        session.state = USSDState.REGISTER_NAME
        await _save(db, session)
        return _con("Enter your Full Name")

    async def handle_register_name(
        self, db: AsyncSession, session: USSDSession, user_input: str
    ) -> PlainTextResponse:
        session.full_name = user_input
        session.state = USSDState.REGISTER_PIN
        await _save(db, session)
        return _con("Create a 4-digit PIN")

    async def handle_register_pin(
        self, db: AsyncSession, session: USSDSession, user_input: str
    ) -> PlainTextResponse:
        """PIN must be exactly 4 digits."""
        if not user_input.isdigit() or len(user_input) != 4:
            return _invalid()

        session.pin = user_input
        session.state = USSDState.REGISTER_CONFIRM
        await _save(db, session)
        return _con("Confirm your PIN")

    async def handle_register_confirm(
        self, db: AsyncSession, session: USSDSession, user_input: str
    ) -> PlainTextResponse:
        """PIN confirmation must match the previously entered PIN."""
        if user_input != session.pin:
            return _con("PINs do not match.\nCreate a 4-digit PIN")

        session.state = USSDState.REGISTER_COUNTY
        await _save(db, session)
        return _con("Enter your County (e.g. NAIROBI)")

    async def handle_register_county(
        self, db: AsyncSession, session: USSDSession, user_input: str
    ) -> PlainTextResponse:
        """County must exist in the supported list."""
        county = user_input.upper().replace(" ", "_")
        if county not in COUNTIES:
            return _invalid()

        session.county = county
        session.state = USSDState.REGISTER_BUSINESS
        await _save(db, session)
        return _con(
            "Select Business Type\n"
            "1. Mama Mboga\n"
            "2. Mitumba\n"
            "3. Kibanda Food\n"
            "4. Salon/Barbershop\n"
            "5. Jua Kali\n"
            "6. Electronics/Phones\n"
            "7. Shoes & Bags\n"
            "8. Duka\n"
            "9. Tailoring\n"
            "0. Other"
        )

    async def handle_register_business(
        self, db: AsyncSession, session: USSDSession, user_input: str
    ) -> PlainTextResponse:
        """Business type option must be in the defined map."""
        if user_input not in BUSINESS_OPTIONS:
            return _invalid()

        session.business = BUSINESS_OPTIONS[user_input]
        session.state = USSDState.REGISTER_INCOME
        await _save(db, session)
        return _con(
            "Average Daily Income\n"
            "1. Below 500\n"
            "2. 500 - 1,000\n"
            "3. 1,000 - 3,000\n"
            "4. 3,000 - 10,000\n"
            "5. Above 10,000"
        )

    async def handle_register_income(
        self, db: AsyncSession, session: USSDSession, user_input: str
    ) -> PlainTextResponse:
        """Income option must be in the defined map."""
        if user_input not in INCOME_OPTIONS:
            return _invalid()

        session.income = INCOME_OPTIONS[user_input]
        session.state = USSDState.REGISTER_FREQUENCY
        await _save(db, session)
        return _con(
            "Payment Frequency\n"
            "1. Daily\n"
            "2. Weekly\n"
            "3. Monthly"
        )

    async def handle_register_frequency(
        self, db: AsyncSession, session: USSDSession, user_input: str
    ) -> PlainTextResponse:
        """
        Final registration step.
        Validates frequency, delegates user creation to User Service,
        then triggers Recommendation Service and sends a welcome SMS.
        USSD never implements the business logic itself.
        """
        if user_input not in FREQUENCY_OPTIONS:
            return _invalid()

        session.frequency = FREQUENCY_OPTIONS[user_input]
        await _save(db, session)

        # Delegate user creation to User Service
        try:
            user = await user_services.create_user(
                db,
                UserCreate(
                    national_id=session.national_id,
                    phone_no=session.phone_number,
                    full_name=session.full_name,
                    pin=session.pin,
                    county=session.county,
                    business_type=session.business,
                    income_bracket=session.income,
                    payment_frequency=session.frequency,
                ),
            )
        except ValueError as e:
            return _end(str(e))

        # Delegate recommendation generation to Recommendation Service
        await policy_services.generate_recommendation(db, user)

        # Send welcome SMS via Notification Service (not directly via AT)
        await notification_service.send_welcome_sms(db, user)

        return _end(
            "Registration complete.\n"
            "You will receive an SMS shortly."
        )

    # ─── Login Handlers ───────────────────────────────────────────────────────

    async def handle_login_id(
        self, db: AsyncSession, session: USSDSession, user_input: str
    ) -> PlainTextResponse:
        """Collect National ID during login."""
        if not user_input.isdigit():
            return _invalid()

        session.national_id = user_input
        session.state = USSDState.LOGIN_PIN
        await _save(db, session)
        return _con("Enter your PIN")

    async def handle_login_pin(
        self, db: AsyncSession, session: USSDSession, user_input: str
    ) -> PlainTextResponse:
        """
        Delegate PIN verification to User Service.
        On success, store user_id in session and show dashboard.
        """
        if not user_input.isdigit() or len(user_input) != 4:
            return _invalid()

        # User Service authenticates using phone number (derived from session)
        # and the PIN the user just entered.
        user = await user_services.authenticate_user(
            db, session.phone_number, user_input
        )
        if not user:
            return _end("Invalid National ID or PIN.\nPlease dial again.")

        session.user_id = str(user.id)
        session.state = USSDState.DASHBOARD
        await _save(db, session)
        return self.show_dashboard()

    # ─── Dashboard Handler ────────────────────────────────────────────────────

    async def handle_dashboard(
        self, db: AsyncSession, session: USSDSession, user_input: str
    ) -> PlainTextResponse:
        """Route dashboard menu selections to the appropriate sub-flow."""
        if user_input == "1":
            session.state = USSDState.VIEW_POLICY
            await _save(db, session)
            return await self.handle_view_policy(db, session, user_input)

        if user_input == "2":
            session.state = USSDState.ACTIVATE_POLICY
            await _save(db, session)
            return await self.handle_activate_policy(db, session, user_input)

        if user_input == "3":
            session.state = USSDState.PAY_PREMIUM
            await _save(db, session)
            return await self.handle_pay_premium(db, session, user_input)

        if user_input == "4":
            session.state = USSDState.FILE_CLAIM_TYPE
            await _save(db, session)
            return _con(
                "Claim Type\n"
                "1. Fire\n"
                "2. Theft\n"
                "3. Flood\n"
                "4. Other"
            )

        if user_input == "5":
            session.state = USSDState.HELP
            await _save(db, session)
            return await self.handle_help(db, session, user_input)

        if user_input == "6":
            # Logout: clear session state
            session.user_id = None
            session.state = USSDState.MAIN_MENU
            await _save(db, session)
            return _end("You have been logged out.")

        return _invalid()

    # ─── Policy Handlers ──────────────────────────────────────────────────────

    async def handle_view_policy(
        self, db: AsyncSession, session: USSDSession, user_input: str
    ) -> PlainTextResponse:
        """
        Delegate policy lookup to Policy Service and display the result.
        USSD only formats the response; it does not query the DB directly.
        """
        policy = await policy_services.get_active_policy_for_user(db, session.user_id)
        if not policy:
            return _end("No active policy found.")

        return _end(
            f"Policy: {policy.policy_code}\n"
            f"Coverage: KES {policy.coverage_amount:,.0f}\n"
            f"Premium: KES {policy.premium_amount:,.0f}/{policy.premium_frequency}\n"
            f"Status: {policy.status}\n"
            f"Expires: {policy.expires_at.strftime('%d %b %Y') if policy.expires_at else 'N/A'}"
        )

    async def handle_activate_policy(
        self, db: AsyncSession, session: USSDSession, user_input: str
    ) -> PlainTextResponse:
        """
        Delegate activation instructions to Policy Service.
        USSD only relays the payment instructions back to the user.
        """
        instructions = await policy_services.get_activation_instructions(
            db, session.user_id
        )
        if not instructions:
            return _end("No pending policy to activate.")

        return _end(instructions)

    async def handle_pay_premium(
        self, db: AsyncSession, session: USSDSession, user_input: str
    ) -> PlainTextResponse:
        """
        Delegate payment initiation to Payment Service.
        USSD only tells the user to complete payment via M-Pesa.
        """
        await payment_services.initiate_premium_payment_for_user(
            db, session.user_id
        )
        return _end(
            "Complete your payment using M-Pesa.\n"
            "You will receive a confirmation SMS."
        )

    # ─── Claim Handlers ───────────────────────────────────────────────────────

    async def handle_file_claim_type(
        self, db: AsyncSession, session: USSDSession, user_input: str
    ) -> PlainTextResponse:
        """Validate claim category selection and prompt for description."""
        if user_input not in CLAIM_CATEGORY_OPTIONS:
            return _invalid()

        session.claim_type = CLAIM_CATEGORY_OPTIONS[user_input]
        session.state = USSDState.FILE_CLAIM_DESC
        await _save(db, session)
        return _con("Describe your claim (max 50 chars)")

    async def handle_file_claim_desc(
        self, db: AsyncSession, session: USSDSession, user_input: str
    ) -> PlainTextResponse:
        """
        Collect claim description and delegate submission to Claim Service.
        USSD does not validate the claim itself.
        """
        if len(user_input) > 50:
            return _con("Description too long (max 50 chars).\nTry again.")

        try:
            claim = await claim_services.submit_claim_for_user(
                db,
                user_id=session.user_id,
                category=session.claim_type,
                description=user_input,
            )
        except ValueError as e:
            return _end(str(e))

        return _end(
            f"Claim submitted.\n"
            f"Reference: {claim.claim_code}\n"
            "We will review it shortly."
        )

    # ─── Help Handler ─────────────────────────────────────────────────────────

    async def handle_help(
        self, db: AsyncSession, session: USSDSession, user_input: str
    ) -> PlainTextResponse:
        return _end(
            "SokoSure Support\n"
            "Call: 0800 720 000\n"
            "SMS: 40001"
        )
