import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.models.enums import UserRole
from app.schemas.auth import UserOut
from app.schemas.common import PaginatedResponse
from app.api.deps import get_current_user, require_min_role

router = APIRouter()


@router.get("/", response_model=PaginatedResponse[UserOut])
def list_users(
    role: Optional[UserRole] = None,
    search: Optional[str] = Query(default=None, description="Search by name, email or phone"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(require_min_role(UserRole.STAFF)),
):
    stmt = select(User)
    if role:
        stmt = stmt.where(User.role == role)
    if search:
        like = f"%{search}%"
        stmt = stmt.where((User.full_name.ilike(like)) | (User.email.ilike(like)) | (User.phone.ilike(like)))

    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    items = db.scalars(stmt.order_by(User.created_at.desc()).offset((page - 1) * page_size).limit(page_size)).all()
    return PaginatedResponse.build(items=items, total=total, page=page, page_size=page_size)


@router.get("/{user_id}", response_model=UserOut)
def get_user(user_id: uuid.UUID, db: Session = Depends(get_db), _: User = Depends(require_min_role(UserRole.STAFF))):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.patch("/{user_id}/role", response_model=UserOut)
def change_user_role(
    user_id: uuid.UUID,
    new_role: UserRole,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_min_role(UserRole.ADMIN)),
):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if new_role == UserRole.SUPER_ADMIN and current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Only a super admin can grant super admin role")
    user.role = new_role
    db.commit()
    db.refresh(user)
    return user


@router.patch("/{user_id}/deactivate", response_model=UserOut)
def deactivate_user(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: User = Depends(require_min_role(UserRole.ADMIN)),
):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_active = False
    db.commit()
    db.refresh(user)
    return user
