from uuid import UUID
from datetime import datetime
from pydantic import BaseModel


class UserRequest(BaseModel):
    username: str
    email: str
    password: str


class UserResponse(BaseModel):
    id: UUID
    username: str
    created_at: datetime
    updated_at: datetime
