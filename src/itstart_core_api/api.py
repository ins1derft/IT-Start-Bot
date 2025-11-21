from fastapi import APIRouter

from .auth import router as auth_router

router = APIRouter()


@router.get("/healthz", summary="Liveness probe")
async def healthz() -> dict[str, str]:
    return {"status": "ok"}


router.include_router(auth_router)
