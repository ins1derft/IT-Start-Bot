from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from itstart_domain import PublicationType
from .auth import get_current_admin
from .dependencies import get_db_session
from .repositories import PublicationRepository, TagRepository
from .schemas import PublicationRead

router = APIRouter(prefix="/admin/publications", tags=["publications"])


@router.get("", response_model=list[PublicationRead])
async def list_publications(
    pub_type: PublicationType | None = None,
    session: AsyncSession = Depends(get_db_session),
    current=Depends(get_current_admin),
):
    repo = PublicationRepository(session)
    q = repo.base_query()
    if pub_type:
        q = q.where(repo.model.type == pub_type)
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
    session: AsyncSession = Depends(get_db_session),
    current=Depends(get_current_admin),
):
    repo = PublicationRepository(session)
    pub = await repo.get(pub_id)
    if not pub:
        raise HTTPException(status_code=404, detail="Not found")
    if isinstance(title, str):
        pub.title = title
    if isinstance(description, str):
        pub.description = description
    pub.is_edited = True
    await session.commit()
    await session.refresh(pub)
    return pub
