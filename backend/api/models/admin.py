from pydantic import BaseModel
from .users import UserResponse


class AdminSwitchUserRequest(BaseModel):
    username_to_switch: str


class AdminSwitchUserResponse(BaseModel):
    user: UserResponse
    access_token: str
    type: str
