
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import Any
from datetime import timedelta

from app.core.auth import create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from app.db.base import get_db
from app.schemas.user import User, UserCreate, UserUpdate
from app.services.user_service import (
    authenticate_user,
    create_user,
    get_user_by_email,
    update_user
)

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@router.post("/token")
async def login(
    db: Session = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/register", response_model=User)
def register_user(
    *,
    db: Session = Depends(get_db),
    user_in: UserCreate,
) -> Any:
    user = get_user_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="A user with this email already exists."
        )
    user = create_user(db, user_in)
    return user

@router.get("/me", response_model=User)
def read_user_me(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> Any:
    user = get_current_user(db, token)
    return user

@router.put("/me", response_model=User)
def update_user_me(
    *,
    db: Session = Depends(get_db),
    user_in: UserUpdate,
    token: str = Depends(oauth2_scheme)
) -> Any:
    current_user = get_current_user(db, token)
    user = update_user(db, current_user, user_in)
    return user
