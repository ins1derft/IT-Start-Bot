from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from itstart_domain import AdminRole, PublicationType

from .auth import get_current_admin
from .dependencies import get_db_session
from .repositories import PublicationScheduleRepository
from .schemas import PublicationScheduleRead, PublicationScheduleUpdate

router = APIRouter(prefix="/admin/schedule", tags=["schedule"])


async def _ensure_defaults(repo: PublicationScheduleRepository) -> None:
    defaults = {
        PublicationType.job: 360,
        PublicationType.internship: 1440,
        PublicationType.conference: 1440,
        PublicationType.contest: 1440,
    }
    for ptype, interval in defaults.items():
        await repo.upsert(ptype, interval_minutes=interval, start_time=None, is_active=True)


@router.get("/publications", response_model=list[PublicationScheduleRead])
async def get_publication_schedule(
    session: AsyncSession = Depends(get_db_session),
    current=Depends(get_current_admin),
):
    if current.role != AdminRole.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    repo = PublicationScheduleRepository(session)
    result = await session.execute(repo.base_query())
    rows = list(result.scalars())
    if not rows:
        await _ensure_defaults(repo)
        await session.commit()
        result = await session.execute(repo.base_query())
        rows = list(result.scalars())
    return rows


@router.patch("/publications", response_model=list[PublicationScheduleRead])
async def update_publication_schedule(
    payload: PublicationScheduleUpdate,
    session: AsyncSession = Depends(get_db_session),
    current=Depends(get_current_admin),
):
    if current.role != AdminRole.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    repo = PublicationScheduleRepository(session)
    await _ensure_defaults(repo)

    if payload.job_interval_minutes is not None:
        await repo.upsert(PublicationType.job, interval_minutes=payload.job_interval_minutes)
    if payload.internship_interval_minutes is not None:
        await repo.upsert(
            PublicationType.internship, interval_minutes=payload.internship_interval_minutes
        )
    if payload.conference_interval_minutes is not None:
        await repo.upsert(
            PublicationType.conference, interval_minutes=payload.conference_interval_minutes
        )
    if payload.contest_interval_minutes is not None:
        await repo.upsert(
            PublicationType.contest, interval_minutes=payload.contest_interval_minutes
        )

    await session.commit()
    result = await session.execute(repo.base_query())
    return list(result.scalars())
