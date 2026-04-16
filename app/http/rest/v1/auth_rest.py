from app.core.config import settings
from fastapi import APIRouter, HTTPException, status
from app.core.common.application.dto import GoogleLoginData, DevLoginData
from app.business import AuthBusiness


auth_v1 = APIRouter(
    prefix=f"{settings.API_V1_STR}/auth",
    tags=["auth"],
)

@auth_v1.post("/google-login")
async def google_login(
    data: GoogleLoginData,
):
    return await AuthBusiness.google_login_service(data)

@auth_v1.post("/dev-login")
async def dev_login(data: DevLoginData):
    if not settings.APP_DEBUG:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This endpoint is only available in debug mode.",
        )
    return await AuthBusiness.dev_login_service(data)