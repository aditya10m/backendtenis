from pydantic import BaseModel, EmailStr
from uuid import UUID

class UserRegister(BaseModel):
    email: EmailStr
    password: str
    full_name: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: UUID
    email: EmailStr
    full_name: str
    is_coach: bool
    role: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse
