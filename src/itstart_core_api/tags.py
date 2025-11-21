from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from itstart_domain import TagCategory
from .auth import get_current_admin
from .dependencies import get_db_session
from .repositories import TagRepository
from .schemas import TagRead

router = APIRouter(prefix="/admin/tags", tags=["tags"])


@router.get("", response_model=list[TagRead])
async def list_tags(
    category: TagCategory | None = None,
    session: AsyncSession = Depends(get_db_session),
    current=Depends(get_current_admin),
):
    repo = TagRepository(session)
    q = repo.base_query()
    if category:
        q = q.where(repo.model.category == category)
    result = await session.execute(q)
    return list(result.scalars())


@router.post("", response_model=TagRead, status_code=201)
async def create_tag(
    name: str,
    category: TagCategory,
    session: AsyncSession = Depends(get_db_session),
    current=Depends(get_current_admin),
):
    repo = TagRepository(session)
    exists = await repo.get_by_name_category(name, category)
    if exists:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tag exists")
    tag = repo.create(name=name, category=category)
    await session.commit()
    await session.refresh(tag)
    return tag


@router.patch("/{tag_id}", response_model=TagRead)
async def update_tag(
    tag_id: UUID,
    name: str,
    category: TagCategory,
    session: AsyncSession = Depends(get_db_session),
    current=Depends(get_current_admin),
):
    repo = TagRepository(session)
    tag = await session.get(repo.model, tag_id)
    if not tag:
        raise HTTPException(status_code=404, detail="Not found")
    tag.name = name
    tag.category = category
    await session.commit()
    await session.refresh(tag)
    return tag


@router.delete("/{tag_id}", status_code=204)
async def delete_tag(
    tag_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    current=Depends(get_current_admin),
):
    repo = TagRepository(session)
    tag = await session.get(repo.model, tag_id)
    if not tag:
        raise HTTPException(status_code=404, detail="Not found")
    await session.delete(tag)
    await session.commit()
    return None
