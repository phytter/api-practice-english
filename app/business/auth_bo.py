from datetime import datetime, timedelta, timezone
from typing import Optional
from google.oauth2 import id_token
from google.auth.transport import requests
from fastapi import HTTPException, status, Depends, Request
from jose import JWTError, jwt
from fastapi.security import OAuth2AuthorizationCodeBearer

from app.core.common.application.dto import GoogleLoginData
from app.core.users.application.dto.user_dto import UserOut
from app.core.config import settings
from app.core.users.infra.database.repositories import UserMongoRepository
from app.core.users.domain import UserEntity, UserProgress
from app.core.users.application import UserMapper

class AuthBusiness:

    oauth2_scheme = OAuth2AuthorizationCodeBearer(
        authorizationUrl="https://accounts.google.com/o/oauth2/v2/auth",
        tokenUrl="https://oauth2.googleapis.com/token"
    )
    user_repo = UserMongoRepository()

    @classmethod
    async def google_login_service(cls, token_data: GoogleLoginData):
        token = token_data.token
        try:
            idinfo = id_token.verify_oauth2_token(
                token, requests.Request(), settings.GOOGLE_CLIENT_ID, 5)
            if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid issuer."
                )
            google_id = idinfo['sub']

            user_entity = await cls.user_repo.find_by_google_id(google_id)
            
            if not user_entity:
                user_entity = UserEntity.create(
                    email=idinfo['email'],
                    name=idinfo['name'],
                    picture=idinfo.get('picture', ''),
                    google_id=idinfo['sub'],
                    achievements=[],
                    created_at=datetime.now(timezone.utc),
                    last_login=datetime.now(timezone.utc),
                    progress=UserProgress()
                )
                await cls.user_repo.create(user_entity)
            else:
                # Update last login
                user_entity.last_login = datetime.now(timezone.utc)
                await cls.user_repo.update(user_entity.id, user_entity)

            user_entity = await cls.user_repo.find_by_google_id(google_id)
            user_dto = UserMapper.to_dto(user_entity)
            access_token = cls.create_access_token(data={"sub": str(user_dto.id)})
            
            return {
                "access_token": access_token,
                "token_type": "bearer",
                "user": user_dto
            }

        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid token"
            )
  
    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(days=15)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(
            to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
        )
        return encoded_jwt

    @staticmethod
    async def get_current_user(
        request: Request,
    ) -> UserOut:
        if request.state.user:
            return request.state.user

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User is not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    @classmethod
    async def validate_auth(
        cls,
        request: Request,
        token: str = Depends(oauth2_scheme),
    ) -> UserOut:

        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])

            user_id: str | None = payload.get("sub")
            if user_id is None:
                raise credentials_exception
        except JWTError:
            raise credentials_exception     

        user_entity = await cls.user_repo.find_by_id(user_id)
        if user_entity is None:
            raise credentials_exception

        request.state.user = UserMapper.to_dto(user_entity)
