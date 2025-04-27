from app.core.config import settings
from fastapi import APIRouter
from app.core.common.application.dto import GoogleLoginData
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