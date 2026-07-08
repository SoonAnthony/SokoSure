import bcrypt
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.users.models import User
from app.features.users.schemas import UserCreate


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


async def create_user(db: AsyncSession, user_data: UserCreate) -> User:
    # Dedup checks — this is your core fraud control
    existing_phone = await get_user_by_phone(db, user_data.phone_no)
    if existing_phone:
        raise ValueError("Phone number already registered")

    existing_national_id = await get_user_by_national_id(db, user_data.national_id)
    if existing_national_id:
        raise ValueError("National ID already registered")

    new_user = User(
        national_id=user_data.national_id,
        phone_no=user_data.phone_no,
        full_name=user_data.full_name,
        hashed_pin=hash_pin(user_data.pin),
        county=user_data.county,
        business_type=user_data.business_type,
        income_bracket=user_data.income_bracket,
        payment_frequency=user_data.payment_frequency,
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user


async def authenticate_user(db: AsyncSession, phone_no: str, pin: str) -> User | None:
    user = await get_user_by_phone(db, phone_no)
    if not user:
        return None

    if not verify_pin_hash(pin, user.hashed_pin):
        user.failed_pin_attempts += 1
        db.add(user)
        await db.commit()
        return None

    # reset on successful login
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