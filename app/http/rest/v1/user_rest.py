from app.core.config import settings
from fastapi import APIRouter, Depends
from app.business import UserBusiness, AuthBusiness
from typing import List
from app.core.users.application.dto.user_dto import UserOut


user_v1 = APIRouter(
    prefix=f"{settings.API_V1_STR}/users",
    tags=["users"],
    dependencies=[Depends(AuthBusiness.validate_auth)]
)

@user_v1.get(
    "/profile",
    response_model=UserOut,
    status_code=200,
)
async def get_user_profile(
    user: UserOut = Depends(AuthBusiness.get_current_user)
) -> UserOut:
    return await UserBusiness.get_user(user.id)
