from uuid import UUID
from datetime import timedelta
from typing import List, Annotated
from sqlmodel import Session, select, desc
from fastapi import APIRouter, Depends, HTTPException, status, Body

from src.database import (
    Users,
    Tokens,
    get_session,
    get_db_manager,
    DatabaseManager,
    KnowledgeBases,
)
from src.constants import UserRole
from src.utils import get_formatted_logger
from .user_router import (
    get_current_user,
    create_access_token,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)
from api.models import (
    UserResponse,
    AdminSwitchUserResponse,
    AdminSwitchUserRequest,
    AdminCreateTokenRequest,
    AdminCreateTokenResponse,
)

logger = get_formatted_logger(__file__)

admin_router = APIRouter()


@admin_router.get("/users", response_model=List[UserResponse])
async def get_all_users(
    current_user: Annotated[Users, Depends(get_current_user)],
    db_session: Annotated[Session, Depends(get_session)],
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
    current_user: Annotated[Users, Depends(get_current_user)],
    db_session: Annotated[Session, Depends(get_session)],
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


@admin_router.delete("/users/{user_id}")
async def delete_user(
    user_id: UUID,
    current_user: Annotated[Users, Depends(get_current_user)],
    db_session: Annotated[Session, Depends(get_session)],
    db_manager: Annotated[DatabaseManager, Depends(get_db_manager)],
):
    logger.info(f"Deleting user with id: {user_id}")

    if current_user.id == user_id:
        logger.error("Cannot delete own user!")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete yourself!",
        )

    user_id = str(user_id)

    if current_user.role != UserRole.ADMIN:
        logger.error("Unauthorized access to delete user!")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to access this resource!",
        )

    with db_session as session:
        query = select(Users).where(Users.id == user_id)
        user = session.exec(query).first()

        if user is None:
            logger.error(f"User with id {user_id} not found!")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found!",
            )

        # Get all knowledge bases associated with the user and delete them
        query = select(KnowledgeBases).where(KnowledgeBases.user_id == user_id)

        knowledge_bases = session.exec(query).all()

        # Delete all knowledge bases since all data of each user is within knowledge bases
        for kb in knowledge_bases:
            db_manager.delete_knowledge_base(kb.id)
            session.delete(kb)
            session.commit()

        # Delete the user
        session.delete(user)
        session.commit()

        return {"message": "User deleted successfully!"}


@admin_router.get("/tokens", response_model=List[Tokens])
async def get_all_tokens(
    current_user: Annotated[Users, Depends(get_current_user)],
    db_session: Annotated[Session, Depends(get_session)],
):
    logger.info("Getting all tokens ...")

    if current_user.role != UserRole.ADMIN:
        logger.error("Unauthorized access to get all tokens!")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to access this resource!",
        )

    with db_session as session:
        query = select(Tokens).order_by(desc(Tokens.created_at))
        tokens = session.exec(query).all()
        return tokens


@admin_router.post(
    "/create-token",
    response_model=AdminCreateTokenResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_user_token(
    admin_create_token_request: Annotated[AdminCreateTokenRequest, Body(...)],
    current_user: Annotated[Users, Depends(get_current_user)],
    db_session: Annotated[Session, Depends(get_session)],
):
    username = admin_create_token_request.username
    logger.info(f"Creating token for user: {username}")

    if current_user.role != UserRole.ADMIN:
        logger.error("Unauthorized access to create token!")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to access this resource!",
        )

    with db_session as session:
        query = select(Users).where(Users.username == username)
        user = session.exec(query).first()

        if user is None:
            logger.error(f"User {username} not found!")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found!",
            )

        if user.role == UserRole.ADMIN:
            logger.warning("Admin don't need long term token!")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Admin doesn't need this token!",
            )

        access_token = create_access_token(
            data={"sub": user.username}, long_term_token=True
        )

        added_token = Tokens(
            token=access_token, user_id=user.id, username=user.username, role=user.role
        )

        session.add(added_token)
        session.commit()
        session.refresh(added_token)

        return AdminCreateTokenResponse(
            user_id=user.id,
            username=added_token.username,
            role=added_token.role,
            token=access_token,
            type=added_token.token_type,
            created_at=added_token.created_at,
            updated_at=added_token.updated_at,
        )


@admin_router.delete("/delete-token/{token_id}")
async def delete_token(
    token_id: UUID,
    current_user: Annotated[Users, Depends(get_current_user)],
    db_session: Annotated[Session, Depends(get_session)],
):
    logger.info(f"Deleting token with id: {token_id}")

    if current_user.role != UserRole.ADMIN:
        logger.error("Unauthorized access to delete token!")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to access this resource!",
        )

    with db_session as session:
        query = select(Tokens).where(Tokens.id == token_id)
        token = session.exec(query).first()

        if token is None:
            logger.error(f"Token with id {token_id} not found!")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Token not found!",
            )

        session.delete(token)
        session.commit()

        return {"message": "Token deleted successfully!"}
