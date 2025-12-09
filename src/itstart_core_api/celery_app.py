from __future__ import annotations

import asyncio
import datetime
import logging
from typing import Any

from celery import Celery
from celery.schedules import crontab
from sentry_sdk import init as sentry_init
from sentry_sdk.integrations.celery import CeleryIntegration
from sqlalchemy import select

from .config import get_settings
from .db import build_engine, build_session_maker
from .models import PublicationSchedule

logger = logging.getLogger(__name__)


async def _fetch_publication_schedules() -> list[PublicationSchedule]:
    settings = get_settings()
    engine = build_engine(settings)
    Session = build_session_maker(engine)
    async with Session() as session:
        result = await session.execute(
            select(PublicationSchedule).where(PublicationSchedule.is_active.is_(True))
        )
        return list(result.scalars())


def _build_beat_schedule(settings) -> dict[str, Any]:
    """Compose Celery beat schedule from DB rows; fallback to sane defaults."""
    schedule: dict[str, Any] = {
        "send-deadline-reminders-daily": {
            "task": "itstart_core_api.tasks.send_deadline_reminders",
            "schedule": crontab(hour=0, minute=0),
        },
        "cleanup-old-publications-daily": {
            "task": "itstart_core_api.tasks.cleanup_old_publications",
            "schedule": crontab(hour=3, minute=0),
        },
    }

    try:
        schedules = asyncio.run(_fetch_publication_schedules())
    except Exception:
        logger.exception("Failed to load publication schedules; using fallback interval")
        schedules = []

    if schedules:
        for row in schedules:
            key = f"send-publications-{getattr(row.publication_type, 'value', row.publication_type)}"
            schedule[key] = {
                "task": "itstart_core_api.tasks.send_publications",
                "schedule": datetime.timedelta(minutes=row.interval_minutes),
            }
    else:
        schedule["send-publications-default"] = {
            "task": "itstart_core_api.tasks.send_publications",
            "schedule": datetime.timedelta(minutes=settings.publication_fallback_interval_minutes),
        }
    return schedule


def make_celery() -> Celery:
    settings = get_settings()
    if settings.sentry_dsn:
        sentry_init(
            dsn=settings.sentry_dsn,
            traces_sample_rate=1.0,
            integrations=[CeleryIntegration()],
        )

    app = Celery(
        "itstart_core_api",
        broker=settings.celery_broker_url,
        backend=settings.celery_result_backend or None,
        include=["itstart_core_api.tasks"],
    )
    app.conf.update(
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="UTC",
        enable_utc=True,
        beat_schedule=_build_beat_schedule(settings),
    )
    return app


celery_app = make_celery()


@celery_app.task(name="itstart_core_api.tasks.send_publications")
def send_publications_task():
    from .tasks import send_publications

    asyncio.run(send_publications())


@celery_app.task(name="itstart_core_api.tasks.send_deadline_reminders")
def send_deadline_reminders_task():
    from .tasks import send_deadline_reminders

    asyncio.run(send_deadline_reminders())


@celery_app.task(name="itstart_core_api.tasks.cleanup_old_publications")
def cleanup_old_publications_task():
    from .tasks import cleanup_old_publications

    asyncio.run(cleanup_old_publications())
