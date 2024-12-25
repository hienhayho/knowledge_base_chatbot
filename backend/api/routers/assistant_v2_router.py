import time
from uuid import UUID
from typing import Annotated
from sqlmodel import Session, select, desc
from fastapi import APIRouter, Depends, HTTPException, status, Body

from .user_router import get_current_user
from src.database import (
    get_session,
    Users,
    Assistants,
    Conversations,
)
from src.constants import ApiResponse
from api.services import AssistantService
from api.models import ChatMessage

assistant_v2_router = APIRouter()


@assistant_v2_router.post("/conversation")
async def create_conversation(
    current_user: Annotated[Users, Depends(get_current_user)],
    db_session: Annotated[Session, Depends(get_session)],
):
    with db_session as session:
        assistant = session.exec(
            select(Assistants).where(Assistants.user_id == current_user.id)
        ).first()

        if not assistant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Assistant not found"
            )

        new_conversation = Conversations(
            assistant_id=assistant.id, user_id=current_user.id
        )
        session.add(new_conversation)
        session.commit()
        return new_conversation


@assistant_v2_router.get("/conversations")
async def get_assistant_conversations(
    current_user: Annotated[Users, Depends(get_current_user)],
    db_session: Annotated[Session, Depends(get_session)],
):
    with db_session as session:
        query = select(Assistants).where(Assistants.user_id == current_user.id)

        assistant = session.exec(query).first()
        if not assistant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Assistant not found"
            )

        query = (
            select(Conversations)
            .where(Conversations.assistant_id == assistant.id)
            .order_by(desc(Conversations.updated_at))
        )
        conversations = session.exec(query).all()
        return conversations


@assistant_v2_router.post(
    "/conversations/{conversation_id}/production_messages",
    response_model=ApiResponse,
)
async def production_send_message(
    conversation_id: UUID,
    message: Annotated[ChatMessage, Body(...)],
    current_user: Annotated[Users, Depends(get_current_user)],
    assistant_service: Annotated[AssistantService, Depends()],
    db_session: Annotated[Session, Depends(get_session)],
):
    with db_session as session:
        assistant = session.exec(
            select(Assistants).where(Assistants.user_id == current_user.id)
        ).first()

        if not assistant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Assistant not found"
            )

        conversation_id = str(conversation_id)

        start_time = time.time()
        result = await assistant_service.achat_with_assistant(
            conversation_id,
            current_user.id,
            message=message,
            start_time=start_time,
            use_parser=True,
        )

        return ApiResponse(
            data=result,
            status_message="Successfully!",
            http_code=status.HTTP_200_OK,
            status_code=0,
            extra_info={
                "respone_time": time.time() - start_time,
            },
        )
