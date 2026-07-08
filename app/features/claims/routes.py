from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.features.claims import services as claim_services
from app.features.claims.schemas import (
    ClaimCreate,
    ClaimListResponse,
    ClaimRead,
    ClaimStatusUpdate,
)

router = APIRouter()


@router.post("", response_model=ClaimRead, status_code=status.HTTP_201_CREATED)
async def submit_claim(payload: ClaimCreate, db: AsyncSession = Depends(get_session)):
    try:
        claim = await claim_services.submit_claim(db, payload)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return claim


@router.get("/{claim_id}", response_model=ClaimRead)
async def get_claim(claim_id: UUID, db: AsyncSession = Depends(get_session)):
    claim = await claim_services.get_claim_by_id(db, claim_id)
    if not claim:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Claim not found")
    return claim


@router.get("/user/{user_id}", response_model=ClaimListResponse)
async def get_user_claims(user_id: UUID, db: AsyncSession = Depends(get_session)):
    claims = await claim_services.get_claims_by_user_id(db, user_id)
    return {"claims": claims}


@router.patch("/{claim_id}", response_model=ClaimRead)
async def update_claim(claim_id: UUID, payload: ClaimStatusUpdate, db: AsyncSession = Depends(get_session)):
    claim = await claim_services.update_claim_status(db, claim_id, payload.status)
    if not claim:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Claim not found")
    return claim
