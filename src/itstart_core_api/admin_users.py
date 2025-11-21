from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from itstart_domain import AdminRole

from .auth import get_current_admin
from .dependencies import get_db_session
from .repositories import AdminAuditRepository, AdminUserRepository
from .schemas import AdminUserRead
from .security import hash_password

router = APIRouter(prefix="/admin/users", tags=["admin-users"])


@router.get("", response_model=list[AdminUserRead])
async def list_users(
    current=Depends(get_current_admin),
    session: AsyncSession = Depends(get_db_session),
):
    repo = AdminUserRepository(session)
    # “admin” can list; moderator can’t
    if current.role != AdminRole.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    result = await session.execute(repo.base_query())
    return list(result.scalars())


@router.post("", response_model=AdminUserRead, status_code=201)
async def create_user(
    username: str,
    password: str,
    role: AdminRole,
    session: AsyncSession = Depends(get_db_session),
    current=Depends(get_current_admin),
):
    if current.role != AdminRole.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    repo = AdminUserRepository(session)
    audit = AdminAuditRepository(session)
    exists = await repo.get_by_username(username)
    if exists:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username exists")
    user = repo.create(username=username, password_hash=hash_password(password), role=role)
    await session.commit()
    await session.refresh(user)
    audit.log(
        admin_id=current.id,
        action="create_admin_user",
        target_type="admin_user",
        target_id=user.id,
        details=f"role={role}",
    )
    await session.commit()
    return user


@router.patch("/{user_id}", response_model=AdminUserRead)
async def update_user(
    user_id: UUID,
    role: AdminRole | None = None,
    is_active: bool | None = None,
    password: str | None = None,
    session: AsyncSession = Depends(get_db_session),
    current=Depends(get_current_admin),
):
    if current.role != AdminRole.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    repo = AdminUserRepository(session)
    audit = AdminAuditRepository(session)
    user = await repo.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Not found")
    pwd_hash = hash_password(password) if password else None
    await repo.patch(user, role=role, is_active=is_active, password_hash=pwd_hash)
    await session.commit()
    await session.refresh(user)
    audit.log(
        admin_id=current.id,
        action="update_admin_user",
        target_type="admin_user",
        target_id=user.id,
        details=f"role={role},is_active={is_active},pwd_changed={bool(password)}",
    )
    await session.commit()
    return user


@router.delete("/{user_id}", status_code=204)
async def disable_user(
    user_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    current=Depends(get_current_admin),
):
    if current.role != AdminRole.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    repo = AdminUserRepository(session)
    audit = AdminAuditRepository(session)
    user = await repo.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Not found")
    user.is_active = False
    await session.commit()
    audit.log(
        admin_id=current.id,
        action="disable_admin_user",
        target_type="admin_user",
        target_id=user.id,
        details=None,
    )
    await session.commit()
    return None
