from datetime import UTC, datetime
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.schemas.user import Token, UserCreate, UserLogin, UserResponse
from app.services.auth import (
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])
logger = logging.getLogger(__name__)


@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def signup(payload: UserCreate, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(User).where(User.email == payload.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        email=payload.email,
        password_hash=hash_password(payload.password),
        full_name=payload.full_name,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    logger.info("User signed up: %s", user.email)
    return user


@router.post("/login", response_model=Token)
async def login(payload: UserLogin, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(payload.password, user.password_hash):
        logger.warning("Failed login attempt for: %s", payload.email)
        raise HTTPException(status_code=401, detail="Invalid credentials")

    user.last_login_at = datetime.now(UTC)
    await db.commit()
    token = create_access_token(data={"sub": str(user.user_id)})
    logger.info("User logged in: %s", user.email)
    return Token(access_token=token)


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user
