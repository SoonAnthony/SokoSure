import bcrypt
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.users.models import User
from app.features.users.schemas import UserCreate, UserCreateUSSD, UserCompleteProfile


def hash_pin(pin: str) -> str:
    return bcrypt.hashpw(pin.encode(), bcrypt.gensalt()).decode()


def verify_pin_hash(pin: str, hashed_pin: str) -> bool:
    return bcrypt.checkpw(pin.encode(), hashed_pin.encode())


async def get_user_by_phone(db: AsyncSession, phone_no: str) -> User | None:
    result = await db.execute(select(User).where(User.phone_no == phone_no))
    return result.scalar_one_or_none()


async def get_user_by_national_id(db: AsyncSession, national_id: str) -> User | None:
    result = await db.execute(select(User).where(User.national_id == national_id))
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: UUID) -> User | None:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def create_user_from_ussd(db: AsyncSession, data: UserCreateUSSD) -> User:
    """
    Called at the end of USSD registration.
    Only requires national_id, phone_no, and PIN.
    Profile fields are completed later via SMS/web.
    """
    if await get_user_by_phone(db, data.phone_no):
        raise ValueError("Phone number already registered")
    if await get_user_by_national_id(db, data.national_id):
        raise ValueError("National ID already registered")

    user = User(
        national_id=data.national_id,
        phone_no=data.phone_no,
        hashed_pin=hash_pin(data.pin),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def complete_profile(db: AsyncSession, user_id: UUID, data: UserCompleteProfile) -> User | None:
    """Update the profile fields after USSD registration."""
    user = await get_user_by_id(db, user_id)
    if not user:
        return None

    user.full_name = data.full_name
    user.county = data.county
    user.business_type = data.business_type
    user.income_bracket = data.income_bracket
    user.payment_frequency = data.payment_frequency
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def create_user(db: AsyncSession, user_data: UserCreate) -> User:
    """Full creation used by REST API / admin."""
    if await get_user_by_phone(db, user_data.phone_no):
        raise ValueError("Phone number already registered")
    if await get_user_by_national_id(db, user_data.national_id):
        raise ValueError("National ID already registered")

    user = User(
        national_id=user_data.national_id,
        phone_no=user_data.phone_no,
        hashed_pin=hash_pin(user_data.pin),
        full_name=user_data.full_name,
        county=user_data.county,
        business_type=user_data.business_type,
        income_bracket=user_data.income_bracket,
        payment_frequency=user_data.payment_frequency,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def authenticate_user(db: AsyncSession, phone_no: str, pin: str) -> User | None:
    user = await get_user_by_phone(db, phone_no)
    if not user:
        return None

    if not verify_pin_hash(pin, user.hashed_pin):
        user.failed_pin_attempts += 1
        db.add(user)
        await db.commit()
        return None

    if user.failed_pin_attempts > 0:
        user.failed_pin_attempts = 0
        db.add(user)
        await db.commit()

    return user


async def update_pin(db: AsyncSession, user_id: UUID, new_pin: str) -> User | None:
    user = await get_user_by_id(db, user_id)
    if not user:
        return None

    user.hashed_pin = hash_pin(new_pin)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user