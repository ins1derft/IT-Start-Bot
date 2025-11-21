from __future__ import annotations

import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from itstart_domain import AdminRole, ParserType
from sqlalchemy.ext.asyncio import AsyncSession

from .auth import get_current_admin
from .dependencies import get_db_session
from .repositories import AdminAuditRepository, ParserRepository
from .schemas import ParserRead

router = APIRouter(prefix="/admin/parsers", tags=["parsers"])


@router.get("", response_model=list[ParserRead])
async def list_parsers(
    session: AsyncSession = Depends(get_db_session),
    current=Depends(get_current_admin),
):
    if current.role != AdminRole.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    repo = ParserRepository(session)
    result = await session.execute(repo.base_query())
    return list(result.scalars())


@router.post("", response_model=ParserRead, status_code=201)
async def create_parser(
    source_name: str,
    executable_file_path: str,
    type: ParserType,
    parsing_interval: int,
    parsing_start_time: datetime.datetime,
    is_active: bool = True,
    session: AsyncSession = Depends(get_db_session),
    current=Depends(get_current_admin),
):
    if current.role != AdminRole.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    repo = ParserRepository(session)
    audit = AdminAuditRepository(session)
    parser = repo.create(
        source_name=source_name,
        executable_file_path=executable_file_path,
        type=type,
        parsing_interval=parsing_interval,
        parsing_start_time=parsing_start_time,
        is_active=is_active,
    )
    await session.commit()
    await session.refresh(parser)
    audit.log(admin_id=current.id, action="create_parser", target_type="parser", target_id=parser.id, details=f"type={type}")
    await session.commit()
    return parser


@router.patch("/{parser_id}", response_model=ParserRead)
async def update_parser(
    parser_id: UUID,
    source_name: str | None = None,
    executable_file_path: str | None = None,
    type: ParserType | None = None,
    parsing_interval: int | None = None,
    parsing_start_time: datetime.datetime | None = None,
    is_active: bool | None = None,
    session: AsyncSession = Depends(get_db_session),
    current=Depends(get_current_admin),
):
    if current.role != AdminRole.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    repo = ParserRepository(session)
    audit = AdminAuditRepository(session)
    parser = await repo.get(parser_id)
    if not parser:
        raise HTTPException(status_code=404, detail="Not found")
    await repo.update(
        parser,
        source_name=source_name,
        executable_file_path=executable_file_path,
        type=type,
        parsing_interval=parsing_interval,
        parsing_start_time=parsing_start_time,
        is_active=is_active,
    )
    await session.commit()
    await session.refresh(parser)
    audit.log(admin_id=current.id, action="update_parser", target_type="parser", target_id=parser.id, details="patched")
    await session.commit()
    return parser


@router.post("/{parser_id}/enable", status_code=204)
async def enable_parser(
    parser_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    current=Depends(get_current_admin),
):
    if current.role != AdminRole.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    repo = ParserRepository(session)
    audit = AdminAuditRepository(session)
    parser = await repo.get(parser_id)
    if not parser:
        raise HTTPException(status_code=404, detail="Not found")
    parser.is_active = True
    await session.commit()
    audit.log(admin_id=current.id, action="enable_parser", target_type="parser", target_id=parser.id, details=None)
    await session.commit()
    return None


@router.post("/{parser_id}/disable", status_code=204)
async def disable_parser(
    parser_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    current=Depends(get_current_admin),
):
    if current.role != AdminRole.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    repo = ParserRepository(session)
    audit = AdminAuditRepository(session)
    parser = await repo.get(parser_id)
    if not parser:
        raise HTTPException(status_code=404, detail="Not found")
    parser.is_active = False
    await session.commit()
    audit.log(admin_id=current.id, action="disable_parser", target_type="parser", target_id=parser.id, details=None)
    await session.commit()
    return None
