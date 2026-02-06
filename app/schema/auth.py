from pydantic import BaseModel, EmailStr, field_validator, Field
from typing import Optional
import uuid

# schemas in python -> type validation


#EXPECT email, username, password from frontend (verified username and password length and constraints here)
class UserCreate(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8, max_length=128)
    
    @field_validator('username')
    @classmethod
    def validate_username(cls, v: str) -> str:
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('Username can only contain letters, numbers, hyphens and underscores')
        return v.lower()


# access token for auth
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int

class TokenData(BaseModel):
    username: Optional[str] = None


# /users/me
class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    username: str
    role: str
    
    class Config:
        from_attributes = True