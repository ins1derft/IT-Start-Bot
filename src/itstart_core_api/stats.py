from __future__ import annotations

import datetime
from collections import defaultdict
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from itstart_domain import AdminRole
from .auth import get_current_admin
from .dependencies import get_db_session
from .models import (
    Publication,
    PublicationTag,
    Tag,
    TgUser,
    TgUserSubscription,
    ParsingResult,
)


router = APIRouter(prefix="/admin/stats", tags=["stats"])


def _date_range_filter(query, column, date_from: Optional[datetime.date], date_to: Optional[datetime.date]):
    if date_from:
        query = query.where(column >= datetime.datetime.combine(date_from, datetime.time.min))
    if date_to:
        query = query.where(column <= datetime.datetime.combine(date_to, datetime.time.max))
    return query


@router.get("/users")
async def users_stats(
    date_from: Optional[datetime.date] = None,
    date_to: Optional[datetime.date] = None,
    session: AsyncSession = Depends(get_db_session),
    current=Depends(get_current_admin),
):
    if current.role != AdminRole.admin:
        raise HTTPException(status_code=403, detail="Forbidden")

    q_sub = select(func.count()).select_from(TgUser)
    q_sub = _date_range_filter(q_sub.where(TgUser.register_at != None), TgUser.register_at, date_from, date_to)  # noqa: E712

    q_unsub = select(func.count()).select_from(TgUser)
    q_unsub = _date_range_filter(q_unsub.where(TgUser.refused_at != None), TgUser.refused_at, date_from, date_to)  # noqa: E712

    subs = (await session.execute(q_sub)).scalar_one()
    unsubs = (await session.execute(q_unsub)).scalar_one()

    active = (await session.execute(select(func.count()).select_from(TgUser).where(TgUser.refused_at == None))).scalar_one()  # noqa: E711

    return {
        "subscribed": subs,
        "unsubscribed": unsubs,
        "delta": subs - unsubs,
        "active_users": active,
    }


@router.get("/tags/top")
async def tags_top(
    limit: int = 5,
    session: AsyncSession = Depends(get_db_session),
    current=Depends(get_current_admin),
):
    if current.role not in (AdminRole.admin, AdminRole.moderator):
        raise HTTPException(status_code=403, detail="Forbidden")

    q = (
        select(Tag.name, func.count(PublicationTag.tag_id).label("cnt"))
        .join(PublicationTag, PublicationTag.tag_id == Tag.id)
        .group_by(Tag.id)
        .order_by(func.count(PublicationTag.tag_id).desc())
        .limit(limit)
    )
    rows = (await session.execute(q)).all()
    return [{"name": r[0], "count": r[1]} for r in rows]


@router.get("/parsers")
async def parsers_error_percent(
    date_from: Optional[datetime.date] = None,
    date_to: Optional[datetime.date] = None,
    session: AsyncSession = Depends(get_db_session),
    current=Depends(get_current_admin),
):
    if current.role != AdminRole.admin:
        raise HTTPException(status_code=403, detail="Forbidden")

    q = select(ParsingResult.parser_id, ParsingResult.success).select_from(ParsingResult)
    q = _date_range_filter(q, ParsingResult.date, date_from, date_to)
    rows = (await session.execute(q)).all()

    totals = defaultdict(int)
    errors = defaultdict(int)
    for parser_id, success in rows:
        totals[parser_id] += 1
        if not success:
            errors[parser_id] += 1
    result = []
    for pid, total in totals.items():
        err = errors.get(pid, 0)
        percent = (err / total) * 100 if total else 0
        result.append({"parser_id": str(pid), "error_percent": percent, "total": total})
    return result


@router.get("/publications")
async def publications_per_day(
    date_from: Optional[datetime.date] = None,
    date_to: Optional[datetime.date] = None,
    session: AsyncSession = Depends(get_db_session),
    current=Depends(get_current_admin),
):
    if current.role not in (AdminRole.admin, AdminRole.moderator):
        raise HTTPException(status_code=403, detail="Forbidden")

    q = select(func.date(Publication.created_at).label("day"), func.count().label("count")).group_by("day")
    q = _date_range_filter(q, Publication.created_at, date_from, date_to)
    rows = (await session.execute(q)).all()
    return [{"date": str(day), "count": count} for day, count in rows]
