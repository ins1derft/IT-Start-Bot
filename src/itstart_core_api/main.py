from __future__ import annotations

import logging

import sentry_sdk
import uvicorn
from fastapi import FastAPI

from .api import router
from .config import Settings, get_settings
from .db import build_engine, build_session_maker
from .dependencies import get_db_session

logger = logging.getLogger(__name__)


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    if settings.sentry_dsn:
        sentry_sdk.init(dsn=settings.sentry_dsn, traces_sample_rate=1.0)

    engine = build_engine(settings)
    session_maker = build_session_maker(engine)

    app = FastAPI(
        title="ITStart Core API",
        version="0.1.0",
    )

    # Dependency wiring placeholder; once repos are added, inject get_session.
    app.state.engine = engine
    app.state.session_maker = session_maker
    app.dependency_overrides = {
        # Future router deps can pull session via Depends(app.state.get_session)
    }

    app.dependency_overrides = {}
    app.include_router(router, dependencies=[])
    return app


app = create_app()


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
