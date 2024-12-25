from uuid import UUID
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr


class UserLogin(BaseModel):
    username: str = Field(..., min_length=4, max_length=20, description="Username")
    password: str = Field(..., min_length=6, description="Password")


class UserRequest(BaseModel):
    username: str = Field(..., min_length=4, max_length=20, description="Username")
    email: Optional[EmailStr] = Field(None, description="Email")
    password: str = Field(..., min_length=6, description="Password")
    admin_access_token: Optional[str] = Field(None, description="Admin access token")


class UserResponse(BaseModel):
    id: UUID = Field(..., description="User ID")
    username: str = Field(..., description="Username")
    role: str = Field(..., description="Role")
    access_token: Optional[str] = Field(None, description="Access token")
    created_at: datetime = Field(..., description="Created at")
    updated_at: datetime = Field(..., description="Updated at")


class DeleteUserRequest(BaseModel):
    username: str = Field(..., description="Username")
    admin_access_token: str = Field(..., description="Admin access token")
