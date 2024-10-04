from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr


class UserRequest(BaseModel):
    username: str = Field(..., min_length=4, max_length=20, description="Username")
    email: EmailStr = Field(..., description="Email")
    password: str = Field(..., min_length=6, max_length=20, description="Password")


class UserResponse(BaseModel):
    id: UUID = Field(..., description="User ID")
    username: str = Field(..., description="Username")
    created_at: datetime = Field(..., description="Created at")
    updated_at: datetime = Field(..., description="Updated at")
