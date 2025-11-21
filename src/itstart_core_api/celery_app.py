from __future__ import annotations

import asyncio
import logging

from celery import Celery

from .config import get_settings

logger = logging.getLogger(__name__)


def make_celery() -> Celery:
    settings = get_settings()
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
