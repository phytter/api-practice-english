from .base import BaseModel, EmailStr

class GoogleLoginData(BaseModel):
    token: str

class DevLoginData(BaseModel):
    email: EmailStr
    name: str