from __future__ import annotations

import logging

import sentry_sdk
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .admin_users import router as admin_users_router
from .api import router
from .auth import router as auth_router
from .config import Settings, get_settings
from .db import build_engine, build_session_maker
from .export import router as export_router
from .metrics import middleware_factory as metrics_middleware_factory
from .metrics import router as metrics_router
from .parsers import router as parsers_router
from .publications import router as publications_router
from .schedule import router as schedule_router
from .security import hash_password
from .stats import router as stats_router
from .tag_seed import TagRepository, seed_tags
from .tags import router as tags_router
from .repositories import AdminUserRepository
from itstart_domain import AdminRole

logger = logging.getLogger(__name__)


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    if settings.sentry_dsn:
        sentry_sdk.init(dsn=settings.sentry_dsn, traces_sample_rate=1.0)

    engine = build_engine(settings)
    session_maker = build_session_maker(engine)

    tags_metadata = [
        {"name": "auth", "description": "Логин, 2FA, смена пароля, профайл администратора."},
        {"name": "admin-users", "description": "Управление пользователями админки и ролями."},
        {"name": "tags", "description": "Справочник тегов: создание, редактирование, удаление."},
        {"name": "publications", "description": "CRUD публикаций, модерация, ручная отправка."},
        {"name": "parsers", "description": "Управление источниками/агентами парсинга."},
        {"name": "schedule", "description": "Настройки расписаний рассылки публикаций."},
        {"name": "stats", "description": "Статистика пользователей, тегов, парсеров, публикаций."},
        {"name": "export", "description": "Экспорт публикаций в CSV/XLSX."},
        {"name": "metrics", "description": "health/metrics endpoints для мониторинга."},
    ]

    app = FastAPI(
        title="ITStart Core API",
        version="0.1.0",
        openapi_tags=tags_metadata,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://localhost:8000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Dependency wiring placeholder; once repos are added, inject get_session.
    app.state.engine = engine
    app.state.session_maker = session_maker
    app.dependency_overrides = {}
    app.include_router(router, dependencies=[])
    app.include_router(auth_router)
    app.include_router(admin_users_router)
    app.include_router(tags_router)
    app.include_router(publications_router)
    app.include_router(parsers_router)
    app.include_router(stats_router)
    app.include_router(export_router)
    app.include_router(schedule_router)
    app.include_router(metrics_router)

    app.middleware("http")(metrics_middleware_factory())
    return app


app = create_app()


@app.on_event("startup")
async def seed_startup():
    settings = get_settings()
    engine = build_engine(settings)
    Session = build_session_maker(engine)
    async with Session() as session:
        tag_repo = TagRepository(session)
        await seed_tags(tag_repo)

        # Seed default admin user if configured and not present
        if settings.admin_default_username and settings.admin_default_password:
            admin_repo = AdminUserRepository(session)
            existing = await admin_repo.get_by_username(settings.admin_default_username)
            if not existing:
                admin_repo.create(
                    username=settings.admin_default_username,
                    password_hash=hash_password(settings.admin_default_password),
                    role=AdminRole(settings.admin_default_role),
                )
                logger.info(
                    "Created default admin user",
                    extra={"username": settings.admin_default_username},
                )
            else:
                logger.info(
                    "Default admin user already exists; skipping creation",
                    extra={"username": settings.admin_default_username},
                )

        await session.commit()


def run() -> None:
    settings = get_settings()
    logger.info("Starting core API", extra={"host": settings.api_host, "port": settings.api_port})
    uvicorn.run(
        "itstart_core_api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=False,
        log_level="info",
    )


if __name__ == "__main__":
    run()
