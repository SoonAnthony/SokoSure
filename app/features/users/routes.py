from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.core.database import get_session
from app.features.users.schemas import UserCreateUSSD, UserRead, UserLogin, UserCompleteProfile
from app.features.users import services as user_services

router = APIRouter()


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserCreateUSSD,
    db: AsyncSession = Depends(get_session),
):
    try:
        user = await user_services.create_user_from_ussd(db, user_data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return user


@router.post("/login", response_model=UserRead)
async def login_user(
    login_data: UserLogin,
    db: AsyncSession = Depends(get_session),
):
    user = await user_services.authenticate_user(db, login_data.phone_no, login_data.pin)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid phone number or PIN",
        )
    return user


@router.get("/{user_id}", response_model=UserRead)
async def get_user_profile(
    user_id: UUID,
    db: AsyncSession = Depends(get_session),
):
    user = await user_services.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.patch("/{user_id}/profile", response_model=UserRead)
async def complete_profile(
    user_id: UUID,
    data: UserCompleteProfile,
    db: AsyncSession = Depends(get_session),
):
    """Complete the user profile after USSD registration."""
    user = await user_services.complete_profile(db, user_id, data)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.patch("/pin", response_model=UserRead)
async def update_user_pin(
    user_id: UUID,
    new_pin: str,
    db: AsyncSession = Depends(get_session),
):
    user = await user_services.update_pin(db, user_id, new_pin)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user