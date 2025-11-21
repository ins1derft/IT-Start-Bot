from fastapi import APIRouter

router = APIRouter()


@router.get("/healthz", summary="Liveness probe")
async def healthz() -> dict[str, str]:
    return {"status": "ok"}
