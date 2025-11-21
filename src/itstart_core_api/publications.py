from __future__ import annotations

import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from itstart_domain import PublicationType

from .auth import get_current_admin
from .config import get_settings
from .crypto import encrypt_contact_info
from .dependencies import get_db_session
from .models import PublicationTag
from .repositories import AdminAuditRepository, PublicationRepository
from .schemas import PublicationRead

router = APIRouter(prefix="/admin/publications", tags=["publications"])


def _to_pub_read(pub) -> PublicationRead:
    tags = []
    if hasattr(pub, "__dict__") and "tags" in pub.__dict__:
        for pt in pub.tags:
            if hasattr(pt, "tag") and pt.tag:
                tags.append(pt.tag)
    return PublicationRead(
        id=pub.id,
        title=pub.title,
        description=pub.description,
        type=pub.type,
        company=pub.company,
        url=pub.url,
        created_at=pub.created_at,
        vacancy_created_at=pub.vacancy_created_at,
        updated_at=getattr(pub, "updated_at", None),
        is_edited=pub.is_edited,
        is_declined=pub.is_declined,
        deadline_at=getattr(pub, "deadline_at", None),
        contact_info=getattr(pub, "contact_info", None),
        tags=tags,
        status=getattr(pub, "status", ""),
        decline_reason=getattr(pub, "decline_reason", None),
        editor_id=getattr(pub, "editor_id", None),
    )


@router.get("", response_model=list[PublicationRead])
async def list_publications(
    pub_type: PublicationType | None = None,
    status: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    tag_ids: list[UUID] | None = None,
    session: AsyncSession = Depends(get_db_session),
    current=Depends(get_current_admin),
):
    repo = PublicationRepository(session)
    q = repo.base_query().options(selectinload(repo.model.tags).selectinload(PublicationTag.tag))
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
    return [_to_pub_read(p) for p in result.scalars()]


@router.get("/{pub_id}", response_model=PublicationRead)
async def get_publication(pub_id: UUID, session: AsyncSession = Depends(get_db_session), current=Depends(get_current_admin)):
    repo = PublicationRepository(session)
    pub = await repo.get(pub_id)
    if not pub:
        raise HTTPException(status_code=404, detail="Not found")
    return _to_pub_read(pub)


@router.patch("/{pub_id}", response_model=PublicationRead)
async def update_publication(
    pub_id: UUID,
    title: str | None = None,
    description: str | None = None,
    status: str | None = None,
    contact_info: str | None = None,
    deadline_at: datetime.datetime | None = None,
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
    if contact_info is not None:
        settings = get_settings()
        pub.contact_info = contact_info
        pub.contact_info_encrypted = encrypt_contact_info(contact_info, settings.pgp_public_key)
    if deadline_at is not None:
        pub.deadline_at = deadline_at
    pub.is_edited = True
    pub.updated_at = datetime.datetime.utcnow()
    await session.commit()
    await session.refresh(pub)
    audit.log(admin_id=current.id, action="update_publication", target_type="publication", target_id=pub.id, details=f"status={status}")
    await session.commit()
    return _to_pub_read(pub)


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


@router.post("/{pub_id}/approve-and-send", status_code=204)
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
    audit.log(admin_id=current.id, action="approve_and_send", target_type="publication", target_id=pub.id, details=None)
    await session.commit()
    return None
