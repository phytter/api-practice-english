from datetime import datetime, timedelta, timezone
from typing import Optional
from google.oauth2 import id_token
from google.auth.transport import requests
from fastapi import HTTPException, status, Depends
from jose import JWTError, jwt
from fastapi.security import OAuth2AuthorizationCodeBearer

from app.model import UserIn, UserOut, GoogleLoginData, ObjectId
from app.core.config import settings
from .base import Mongo

class AuthBusiness:

    oauth2_scheme = OAuth2AuthorizationCodeBearer(
        authorizationUrl="https://accounts.google.com/o/oauth2/v2/auth",
        tokenUrl="https://oauth2.googleapis.com/token"
    )

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

            user = await Mongo.users.find_one({"google_id": google_id})
            
            if not user:
                user_data = UserIn(
                    email=idinfo['email'],
                    name=idinfo['name'],
                    picture=idinfo.get('picture'),
                    google_id=idinfo['sub'],
                    achievements=[],
                    created_at=datetime.now(timezone.utc),
                    last_login=datetime.now(timezone.utc)
                )
                await Mongo.users.insert_one(user_data.model_dump())
            else:
                # Update last login
                await Mongo.users.update_one(
                    {"google_id": google_id },
                    {"$set": {"last_login": datetime.now(timezone.utc)}}
                )

            user = await Mongo.users.find_one({"google_id": google_id})
            user = UserOut(**user)

            # Create access token
            access_token = cls.create_access_token(data={"sub": str(user.id)})
            
            return {
                "access_token": access_token,
                "token_type": "bearer",
                "user": user
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
        token: str = Depends(oauth2_scheme)
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

        user = await Mongo.users.find_one({"_id": ObjectId(user_id)})
        if user is None:
            raise credentials_exception
        return UserOut(**user)
