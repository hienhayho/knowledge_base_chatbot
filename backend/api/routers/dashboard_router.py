import sys
import uuid
import string

from uuid import UUID
from pathlib import Path
from typing import Annotated
from wordcloud import WordCloud
from sqlmodel import Session, select, func
from fastapi.responses import JSONResponse, FileResponse
from fastapi import APIRouter, Depends, HTTPException, status


sys.path.append(str(Path(__file__).parent.parent.parent))
from .user_router import get_current_user
from .kb_router import DOWNLOAD_FOLDER
from src.database import (
    get_session,
    Users,
    Conversations,
    KnowledgeBases,
    Messages,
    Assistants,
)
from src.constants import SenderType
from api.models import (
    DashboardStaticsResponse,
    KnowledgeBaseStaticsResponse,
    AssistantStaticsResponse,
    ConversationStaticsResponse,
    GetSourceReponse,
)


dashboard_router = APIRouter()


@dashboard_router.get("/", response_model=DashboardStaticsResponse)
async def get_dashboard(
    current_user: Annotated[Users, Depends(get_current_user)],
    db_session: Annotated[Session, Depends(get_session)],
) -> JSONResponse:
    with db_session as session:
        conversations = session.exec(
            select(Conversations).where(Conversations.user_id == current_user.id)
        ).all()

        total_conversations = len(conversations)

        average_assistant_response_time = session.exec(
            select(func.avg(Messages.response_time).label("average_response_time"))
            .join(Conversations, Conversations.id == Messages.conversation_id)
            .join(Assistants, Assistants.id == Conversations.assistant_id)
            .join(KnowledgeBases, KnowledgeBases.id == Assistants.knowledge_base_id)
            .where(
                KnowledgeBases.user_id == current_user.id,
                Messages.sender_type == SenderType.ASSISTANT,
            )
        ).first()

        knowledge_base_statistics = session.exec(
            select(
                KnowledgeBases.id,
                func.count(Messages.id).label("total_user_messages"),
            )
            .join(Assistants, Assistants.knowledge_base_id == KnowledgeBases.id)
            .join(Conversations, Conversations.assistant_id == Assistants.id)
            .join(Messages, Messages.conversation_id == Conversations.id)
            .where(
                KnowledgeBases.user_id == current_user.id,
                Messages.sender_type == SenderType.USER,
            )
            .group_by(KnowledgeBases.id)
        ).all()

        assistant_statistics = session.exec(
            select(
                Assistants.id,
                func.count(Conversations.id).label("number_of_conversations"),
            )
            .join(Conversations, Conversations.assistant_id == Assistants.id)
            .where(Assistants.user_id == current_user.id)
            .group_by(Assistants.id)
        ).all()

        return DashboardStaticsResponse(
            total_conversations=total_conversations,
            conversations_statistics=[
                ConversationStaticsResponse(
                    id=conversation.id,
                    average_session_chat_time=conversation.average_session_chat_time,
                    average_user_messages=conversation.average_user_messages,
                )
                for conversation in conversations
            ],
            assistant_statistics=[
                AssistantStaticsResponse(
                    id=assistant[0],
                    number_of_conversations=assistant[1],
                )
                for assistant in assistant_statistics
            ],
            average_assistant_response_time=round(average_assistant_response_time, 2),
            knowledge_base_statistics=[
                KnowledgeBaseStaticsResponse(
                    id=knowledge_base[0],
                    total_user_messages=knowledge_base[1],
                )
                for knowledge_base in knowledge_base_statistics
            ],
        )


@dashboard_router.get("/wordcloud/kb/{knowledge_base_id}")
async def get_wordcloud_by_kb(
    knowledge_base_id: UUID,
    is_user: bool,
    current_user: Annotated[Users, Depends(get_current_user)],
    db_session: Annotated[Session, Depends(get_session)],
) -> JSONResponse:
    sender_type = SenderType.USER if is_user else SenderType.ASSISTANT

    with db_session as session:
        knowledge_base = session.exec(
            select(KnowledgeBases).where(
                KnowledgeBases.id == knowledge_base_id,
                KnowledgeBases.user_id == current_user.id,
            )
        )

        if not knowledge_base:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Knowledge Base not found",
            )

        text = session.exec(
            select(Messages.content)
            .join(Conversations, Conversations.id == Messages.conversation_id)
            .join(Assistants, Assistants.id == Conversations.assistant_id)
            .join(KnowledgeBases, KnowledgeBases.id == Assistants.knowledge_base_id)
            .where(
                KnowledgeBases.id == knowledge_base_id,
                KnowledgeBases.user_id == current_user.id,
                Messages.sender_type == sender_type,
            )
        ).all()

        content = " ".join(text)
        wordcloud = WordCloud(width=800, height=400, max_words=1000).generate(content)
        image_path = (
            Path(DOWNLOAD_FOLDER)
            / f"{str(knowledge_base_id).replace('-', '_')}_{sender_type}.png"
        )
        wordcloud.to_file(str(image_path))

        return FileResponse(
            path=image_path, filename=image_path.name, media_type="image/jpeg"
        )


@dashboard_router.get("/wordcloud/assistant/{assistant_id}")
async def get_wordcloud_by_assistant(
    assistant_id: UUID,
    is_user: bool,
    current_user: Annotated[Users, Depends(get_current_user)],
    db_session: Annotated[Session, Depends(get_session)],
) -> JSONResponse:
    sender_type = SenderType.USER if is_user else SenderType.ASSISTANT

    with db_session as session:
        assistant = session.exec(
            select(Assistants).where(
                Assistants.id == assistant_id,
                Assistants.user_id == current_user.id,
            )
        )

        if not assistant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assistant not found",
            )

        text = session.exec(
            select(Messages.content)
            .join(Conversations, Conversations.id == Messages.conversation_id)
            .join(Assistants, Assistants.id == Conversations.assistant_id)
            .where(
                Assistants.id == assistant_id,
                Assistants.user_id == current_user.id,
                Messages.sender_type == sender_type,
            )
        ).all()

        content = " ".join(text)
        wordcloud = WordCloud(width=800, height=400, max_words=1000).generate(content)
        image_path = (
            Path(DOWNLOAD_FOLDER)
            / f"{str(assistant_id).replace('-', '_')}_{sender_type}.png"
        )
        wordcloud.to_file(str(image_path))

        return FileResponse(
            path=image_path, filename=image_path.name, media_type="image/jpeg"
        )


@dashboard_router.get("/wordcloud/conversation/{conversation_id}")
async def get_wordcloud_by_conversation(
    conversation_id: UUID,
    is_user: bool,
    current_user: Annotated[Users, Depends(get_current_user)],
    db_session: Annotated[Session, Depends(get_session)],
) -> JSONResponse:
    sender_type = SenderType.USER if is_user else SenderType.ASSISTANT
    print(sender_type)
    with db_session as session:
        conversation = session.exec(
            select(Conversations).where(
                Conversations.id == conversation_id,
                Conversations.user_id == current_user.id,
            )
        )
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found",
            )

        text = session.exec(
            select(Messages.content)
            .join(Conversations, Conversations.id == Messages.conversation_id)
            .where(
                Conversations.id == conversation_id,
                Conversations.user_id == current_user.id,
                Messages.sender_type == sender_type,
            )
        ).all()

        content = " ".join(text)
        content = [c for c in content if c not in string.punctuation]
        content = "".join(content)
        print(content)
        wordcloud = WordCloud(width=800, height=400, max_words=1000).generate(content)
        image_path = (
            Path(DOWNLOAD_FOLDER)
            / f"{str(conversation_id).replace('-', '_')}_{str(uuid.uuid4())}.png"
        )
        wordcloud.to_file(str(image_path))

        print(image_path)

        return FileResponse(
            path=image_path, filename=image_path.name, media_type="image/jpeg"
        )


@dashboard_router.get("/kbs", response_model=list[GetSourceReponse])
async def get_all_knowledge_bases(
    current_user: Annotated[Users, Depends(get_current_user)],
    db_session: Annotated[Session, Depends(get_session)],
):
    with db_session as session:
        knowledge_bases = session.exec(
            select(KnowledgeBases).where(KnowledgeBases.user_id == current_user.id)
        ).all()

        return knowledge_bases


@dashboard_router.get("/assistants", response_model=list[GetSourceReponse])
async def get_all_assistants(
    current_user: Annotated[Users, Depends(get_current_user)],
    db_session: Annotated[Session, Depends(get_session)],
):
    with db_session as session:
        assistants = session.exec(
            select(Assistants).where(Assistants.user_id == current_user.id)
        ).all()

        return assistants


@dashboard_router.get("/conversations", response_model=list[GetSourceReponse])
async def get_all_conversations(
    current_user: Annotated[Users, Depends(get_current_user)],
    db_session: Annotated[Session, Depends(get_session)],
):
    with db_session as session:
        conversations = session.exec(
            select(Conversations).where(Conversations.user_id == current_user.id)
        ).all()

        return conversations
