from fastapi import APIRouter

router = APIRouter()




@router.get("/healthz", summary="Liveness probe (k8s-style)")
async def healthz() -> dict[str, str]:
    return {"status": "ok"}
