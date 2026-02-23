from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.core.dependencies import get_db, require_roles, get_current_user
from app.models.auth import User
from app.schemas.user import UserResponse, UserCreate, UserUpdate, UserRole
from app.services import user as user_service

PAGINATION_MAX_LIMIT = 500
router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/me", response_model=UserResponse)
def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.get("", response_model=List[UserResponse])
def read_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles([UserRole.SUPERADMIN]))
):
    skip = max(0, skip)
    limit = min(max(1, limit), PAGINATION_MAX_LIMIT)
    return user_service.get_users(db, skip=skip, limit=limit)

@router.get("/{user_id}", response_model=UserResponse)
def read_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles([UserRole.SUPERADMIN]))
):
    user = user_service.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    user: UserCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles([UserRole.SUPERADMIN]))
):
    return user_service.create_user(db, user)

@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    user: UserUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles([UserRole.SUPERADMIN]))
):
    return user_service.update_user(db, user_id, user)

@router.delete("/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles([UserRole.SUPERADMIN]))
):
    return user_service.delete_user(db, user_id)