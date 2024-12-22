from uuid import UUID
from datetime import datetime
from pydantic import BaseModel
from .users import UserResponse
from src.constants import UserRole


class AdminSwitchUserRequest(BaseModel):
    username_to_switch: str


class AdminCreateTokenRequest(BaseModel):
    username: str


class AdminCreateTokenResponse(BaseModel):
    id: UUID
    user_id: UUID
    username: str
    role: UserRole
    type: str
    token: str
    created_at: datetime
    updated_at: datetime


class AdminSwitchUserResponse(BaseModel):
    user: UserResponse
    access_token: str
    type: str
