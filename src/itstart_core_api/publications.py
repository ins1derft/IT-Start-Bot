from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import List, Optional

from itstart_domain import PublicationType
from .auth import get_current_admin
from .dependencies import get_db_session
from .repositories import PublicationRepository, TagRepository, AdminAuditRepository
from .schemas import PublicationRead

router = APIRouter(prefix="/admin/publications", tags=["publications"])


@router.get("", response_model=list[PublicationRead])
async def list_publications(
    pub_type: PublicationType | None = None,
    status: str | None = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    tag_ids: Optional[List[UUID]] = None,
    session: AsyncSession = Depends(get_db_session),
    current=Depends(get_current_admin),
):
    repo = PublicationRepository(session)
    q = repo.base_query()
    if pub_type:
        q = q.where(repo.model.type == pub_type)
    if status:
        q = q.where(repo.model.status == status)
    if date_from:
        q = q.where(repo.model.created_at >= date_from)
    if date_to:
        q = q.where(repo.model.created_at <= date_to)
    if tag_ids:
        q = q.join(repo.model.tags).where(repo.model.tags.tag_id.in_(tag_ids))
    result = await session.execute(q.order_by(repo.model.created_at.desc()))
    return list(result.scalars())


@router.get("/{pub_id}", response_model=PublicationRead)
async def get_publication(pub_id: UUID, session: AsyncSession = Depends(get_db_session), current=Depends(get_current_admin)):
    repo = PublicationRepository(session)
    pub = await repo.get(pub_id)
    if not pub:
        raise HTTPException(status_code=404, detail="Not found")
    return pub


@router.patch("/{pub_id}", response_model=PublicationRead)
async def update_publication(
    pub_id: UUID,
    title: str | None = None,
    description: str | None = None,
    status: str | None = None,
    session: AsyncSession = Depends(get_db_session),
    current=Depends(get_current_admin),
):
    repo = PublicationRepository(session)
    audit = AdminAuditRepository(session)
    pub = await repo.get(pub_id)
    if not pub:
        raise HTTPException(status_code=404, detail="Not found")
    if isinstance(title, str):
        pub.title = title
    if isinstance(description, str):
        pub.description = description
    if status:
        pub.status = status
    pub.is_edited = True
    await session.commit()
    await session.refresh(pub)
    audit.log(admin_id=current.id, action="update_publication", target_type="publication", target_id=pub.id, details=f"status={status}")
    await session.commit()
    return pub


@router.post("/{pub_id}/decline", status_code=204)
async def decline_publication(
    pub_id: UUID,
    reason: str,
    session: AsyncSession = Depends(get_db_session),
    current=Depends(get_current_admin),
):
    repo = PublicationRepository(session)
    audit = AdminAuditRepository(session)
    pub = await repo.get(pub_id)
    if not pub:
        raise HTTPException(status_code=404, detail="Not found")
    pub.status = "declined"
    pub.is_declined = True
    pub.decline_reason = reason
    pub.editor_id = current.id
    await session.commit()
    audit.log(admin_id=current.id, action="decline_publication", target_type="publication", target_id=pub.id, details=reason)
    await session.commit()
    return None


@router.post("/{pub_id}/approve-and-send", response_model=PublicationRead)
async def approve_and_send(
    pub_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    current=Depends(get_current_admin),
):
    repo = PublicationRepository(session)
    audit = AdminAuditRepository(session)
    pub = await repo.get(pub_id)
    if not pub:
        raise HTTPException(status_code=404, detail="Not found")
    pub.status = "sent"
    pub.is_declined = False
    pub.decline_reason = None
    pub.editor_id = current.id
    await session.commit()
    await session.refresh(pub)
    audit.log(admin_id=current.id, action="approve_and_send", target_type="publication", target_id=pub.id, details=None)
    await session.commit()
    # TODO: enqueue sending to users/channel via Celery (per ТЗ)
    return pub
