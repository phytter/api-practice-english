from app.core.config import settings
from fastapi import APIRouter


health_v1 = APIRouter(
    prefix=f"{settings.API_V1_STR}/health/check",
    tags=["health"],
)


@health_v1.get("", response_description="Application health")
async def health_check():

    return {"health": "ok"}
