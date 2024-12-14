from datetime import timedelta
from typing import List, Annotated
from sqlmodel import Session, select
from fastapi import APIRouter, Depends, HTTPException, status, Body

from src.database import Users, get_session
from src.constants import UserRole
from src.utils import get_formatted_logger
from .user_router import (
    get_current_user,
    create_access_token,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)
from api.models import UserResponse, AdminSwitchUserResponse, AdminSwitchUserRequest

logger = get_formatted_logger(__file__)

admin_router = APIRouter()


@admin_router.get("/users", response_model=List[UserResponse])
async def get_all_users(
    current_user: Users = Depends(get_current_user),
    db_session: Session = Depends(get_session),
):
    logger.info("Getting all users ...")

    if current_user.role != UserRole.ADMIN:
        logger.error("Unauthorized access to get all users!")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to access this resource!",
        )

    with db_session as session:
        query = select(Users)
        users = session.exec(query).all()
        return users


@admin_router.post("/switch-user", response_model=AdminSwitchUserResponse)
async def switch_user(
    switchUserRequest: Annotated[AdminSwitchUserRequest, Body(...)],
    current_user: Users = Depends(get_current_user),
    db_session: Session = Depends(get_session),
):
    logger.info(f"Switching to user: {switchUserRequest.username_to_switch}")

    if current_user.role != UserRole.ADMIN:
        logger.error("Unauthorized access to switch user!")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to access this resource!",
        )

    with db_session as session:
        query = select(Users).where(
            Users.username == switchUserRequest.username_to_switch
        )
        user = session.exec(query).first()

        if user is None:
            logger.error(f"User {switchUserRequest.username_to_switch} not found!")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found!",
            )

        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.username}, expires_delta=access_token_expires
        )

        return AdminSwitchUserResponse(
            user=UserResponse(
                id=user.id,
                username=user.username,
                role=user.role,
                created_at=user.created_at,
                updated_at=user.updated_at,
            ),
            access_token=access_token,
            type="bearer",
        )
