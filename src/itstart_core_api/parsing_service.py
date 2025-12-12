from __future__ import annotations

import asyncio
import datetime
import json
import logging
import os
import shlex
import sys
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

import sentry_sdk
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from itstart_domain import PublicationType

from .config import Settings
from .models import Parser, ParsingResult, Publication, Tag
from .repositories import ParserRepository, PublicationRepository, TagRepository

logger = logging.getLogger(__name__)


class ParserExecutionError(RuntimeError):
    pass


@dataclass
class NormalizedItem:
    title: str
    company: str
    description: str
    url: str
    type: PublicationType
    created_at: datetime.datetime
    vacancy_created_at: datetime.datetime


@dataclass
class ParserRunStats:
    parser_id: str
    success: bool
    received: int
    saved: int


def _parse_datetime(value: Any, fallback: datetime.datetime) -> datetime.datetime:
    if isinstance(value, datetime.datetime):
        dt = value
    elif isinstance(value, str):
        try:
            dt = datetime.datetime.fromisoformat(value)
        except ValueError:
            return fallback
    elif isinstance(value, int | float):
        dt = datetime.datetime.fromtimestamp(value)
    else:
        return fallback

    if dt.tzinfo:
        dt = dt.astimezone(datetime.timezone.utc).replace(tzinfo=None)
    return dt


def _normalize_item(raw: dict[str, Any], now: datetime.datetime) -> NormalizedItem | None:
    title = str(raw.get("title") or "").strip()
    description = str(raw.get("description") or "").strip()
    url = str(raw.get("url") or "").strip()
    if not title or not description or not url:
        return None

    company = str(raw.get("company") or "Unknown").strip() or "Unknown"
    type_val = raw.get("type") or PublicationType.job.value
    try:
        pub_type = PublicationType(type_val)
    except ValueError:
        pub_type = PublicationType.job

    created_at = _parse_datetime(raw.get("created_at"), now)
    vacancy_created_at = _parse_datetime(raw.get("vacancy_created_at"), created_at)

    return NormalizedItem(
        title=title,
        company=company,
        description=description,
        url=url,
        type=pub_type,
        created_at=created_at,
        vacancy_created_at=vacancy_created_at,
    )


async def _execute_parser_command(command: str, cwd: str | None = None) -> list[dict[str, Any]]:
    tokens = shlex.split(command)
    if tokens and tokens[0] == "python":
        tokens[0] = sys.executable
    elif tokens and tokens[0].endswith(".py"):
        tokens = [sys.executable, *tokens]

    run_cwd = cwd if cwd and os.path.isdir(cwd) else None

    proc = await asyncio.create_subprocess_exec(
        *tokens,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=run_cwd,
    )
    stdout, stderr = await proc.communicate()
    out_text = (stdout or b"").decode()
    err_text = (stderr or b"").decode()
    if proc.returncode != 0:
        raise ParserExecutionError(
            f"Parser command failed with code {proc.returncode}",
            err_text,
        )

    if not out_text.strip():
        return []

    try:
        return json.loads(out_text)
    except json.JSONDecodeError:
        path = out_text.strip()
        if path and os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        raise ParserExecutionError("Parser output is not valid JSON", err_text)


async def _recent_results(session: AsyncSession, parser_id) -> list[ParsingResult]:
    res = await session.execute(
        select(ParsingResult)
        .where(ParsingResult.parser_id == parser_id)
        .order_by(ParsingResult.date.desc())
        .limit(5)
    )
    return list(res.scalars())


def _failure_streak(results: Iterable[ParsingResult]) -> int:
    streak = 0
    for item in results:
        if item.success:
            break
        streak += 1
    return streak


def _is_due(parser: Parser, results: list[ParsingResult], now: datetime.datetime) -> bool:
    if not parser.is_active:
        return False
    if now < parser.parsing_start_time:
        return False
    last_result = results[0] if results else None
    if not last_result:
        return True

    if last_result.success:
        due_at = last_result.date + datetime.timedelta(minutes=parser.parsing_interval)
    else:
        streak = _failure_streak(results)
        delay = 15 if streak == 1 else 45
        due_at = last_result.date + datetime.timedelta(minutes=delay)
    return now >= due_at


def _match_tags(tags: Iterable[Tag], text: str) -> set[Any]:
    haystack = text.casefold()
    return {tag.id for tag in tags if tag.name.casefold() in haystack}


async def _ingest_items(
    session: AsyncSession,
    parser: Parser,
    items: list[dict[str, Any]],
    tags: list[Tag],
) -> int:
    pub_repo = PublicationRepository(session)
    saved = 0
    now = datetime.datetime.utcnow()

    for raw in items:
        normalized = _normalize_item(raw, now)
        if not normalized:
            continue
        duplicate = await pub_repo.exists_duplicate(
            url=normalized.url,
            title=normalized.title,
            company=normalized.company,
            vacancy_created_at=normalized.vacancy_created_at,
        )
        if duplicate:
            continue

        pub = Publication(
            title=normalized.title,
            description=normalized.description,
            type=normalized.type,
            company=normalized.company,
            url=normalized.url,
            source_id=parser.id,
            created_at=normalized.created_at,
            vacancy_created_at=normalized.vacancy_created_at,
            status="new",
            is_declined=False,
        )
        session.add(pub)
        await session.flush()

        tag_ids = _match_tags(tags, f"{normalized.title} {normalized.description}")
        if tag_ids:
            await pub_repo.add_tags(pub.id, tag_ids)

        saved += 1
    return saved


async def run_due_parsers(
    session: AsyncSession, settings: Settings, now: datetime.datetime | None = None
) -> list[ParserRunStats]:
    """Run all parsers that are due, persist publications and parsing results."""

    repo = ParserRepository(session)
    tag_repo = TagRepository(session)
    tags = await tag_repo.get_all()
    parsers = await repo.list_active()
    stats: list[ParserRunStats] = []
    now = now or datetime.datetime.utcnow()

    for parser in parsers:
        recent = await _recent_results(session, parser.id)
        if not _is_due(parser, recent, now):
            continue

        success = False
        received = 0
        saved = 0
        try:
            items = await _execute_parser_command(
                parser.executable_file_path, cwd=settings.parsers_workdir
            )
            received = len(items)
            saved = await _ingest_items(session, parser, items, tags)
            parser.last_parsed_at = now
            success = True
        except Exception as exc:  # pragma: no cover - network/cmd errors
            logger.exception("Parser execution failed", extra={"parser_id": str(parser.id)})
            sentry_sdk.capture_exception(exc)

        session.add(
            ParsingResult(
                date=now,
                parser_id=parser.id,
                success=success,
                received_amount=received,
            )
        )
        await session.commit()
        stats.append(
            ParserRunStats(
                parser_id=str(parser.id), success=success, received=received, saved=saved
            )
        )

    return stats


async def run_parsers_once(
    session_maker: async_sessionmaker[AsyncSession], settings: Settings
) -> list[ParserRunStats]:
    async with session_maker() as session:
        return await run_due_parsers(session, settings)
