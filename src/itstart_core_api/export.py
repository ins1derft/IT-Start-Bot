from __future__ import annotations

import csv
import io
import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from itstart_domain import AdminRole
from .auth import get_current_admin
from .dependencies import get_db_session
from .models import Publication, PublicationTag, Tag

router = APIRouter(prefix="/admin/export", tags=["export"])


@router.get("/publications")
async def export_publications(
    date_from: Optional[datetime.date] = None,
    date_to: Optional[datetime.date] = None,
    fmt: str = "csv",
    session: AsyncSession = Depends(get_db_session),
    current=Depends(get_current_admin),
):
    if current.role != AdminRole.admin:
        raise HTTPException(status_code=403, detail="Forbidden")

    q = select(Publication)
    if date_from:
        q = q.where(Publication.created_at >= datetime.datetime.combine(date_from, datetime.time.min))
    if date_to:
        q = q.where(Publication.created_at <= datetime.datetime.combine(date_to, datetime.time.max))
    pubs = (await session.execute(q)).scalars().all()

    rows = []
    for pub in pubs:
        tag_rows = await session.execute(
            select(Tag.name)
            .join(PublicationTag, PublicationTag.tag_id == Tag.id)
            .where(PublicationTag.publication_id == pub.id)
        )
        tags = ",".join([r[0] for r in tag_rows])
        rows.append(
            [
                str(pub.id),
                pub.title,
                pub.type,
                pub.company,
                pub.url,
                pub.created_at.isoformat(),
                pub.status if hasattr(pub, "status") else "",
                tags,
            ]
        )

    if fmt == "csv":
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(["id", "title", "type", "company", "url", "created_at", "status", "tags"])
        writer.writerows(rows)
        return Response(
            content=buf.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=publications.csv"},
        )
    else:
        raise HTTPException(status_code=400, detail="Unsupported format")
