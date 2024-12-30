import sys
import json
import uuid
import string
import pandas as pd

from uuid import UUID
from pathlib import Path
from typing import Annotated
from wordcloud import WordCloud
from sqlmodel import select, func, desc
from fastapi.responses import JSONResponse, FileResponse
from fastapi import APIRouter, Depends, HTTPException, status


sys.path.append(str(Path(__file__).parent.parent.parent))
from .user_router import get_current_user
from src.database import (
    Users,
    Conversations,
    KnowledgeBases,
    Messages,
    Assistants,
)
from src.constants import SenderType, DOWNLOAD_FOLDER
from api.models import (
    DashboardStaticsResponse,
    KnowledgeBaseStaticsResponse,
    AssistantStaticsResponse,
    ConversationStaticsResponse,
    GetSourceReponse,
)
from api.deps import SessionDeps


dashboard_router = APIRouter()


@dashboard_router.get("", response_model=DashboardStaticsResponse)
async def get_dashboard(
    current_user: Annotated[Users, Depends(get_current_user)],
    db_session: SessionDeps,
) -> JSONResponse:
    conversations = db_session.exec(
        select(Conversations).where(Conversations.user_id == current_user.id)
    ).all()

    messages = [
        db_session.exec(
            select(Messages)
            .where(Messages.conversation_id == conversation.id)
            .order_by(Messages.created_at)
        ).all()
        for conversation in conversations
    ]

    total_conversations = len(conversations)

    average_assistant_response_time = (
        db_session.exec(
            select(func.avg(Messages.response_time).label("average_response_time"))
            .join(Conversations, Conversations.id == Messages.conversation_id)
            .join(Assistants, Assistants.id == Conversations.assistant_id)
            .join(KnowledgeBases, KnowledgeBases.id == Assistants.knowledge_base_id)
            .where(
                KnowledgeBases.user_id == current_user.id,
                Messages.sender_type == SenderType.ASSISTANT,
            )
        ).first()
        or 0
    )

    knowledge_base_statistics = db_session.exec(
        select(
            KnowledgeBases.id,
            KnowledgeBases.name,
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

    assistant_statistics = db_session.exec(
        select(
            Assistants.id,
            Assistants.name,
            func.count(Conversations.id).label("number_of_conversations"),
        )
        .join(Conversations, Conversations.assistant_id == Assistants.id)
        .where(Assistants.user_id == current_user.id)
        .group_by(Assistants.id)
    ).all()

    # Save all data to excel
    df = pd.DataFrame(
        [
            {
                "total_conversations": total_conversations,
                "average_assistant_response_time": average_assistant_response_time,
                "knowledge_base_statistics": json.dumps(
                    [
                        {
                            "id": str(knowledge_base[0]),
                            "name": knowledge_base[1],
                            "total_user_messages": knowledge_base[2],
                        }
                        for knowledge_base in knowledge_base_statistics
                    ]
                ),
                "assistant_statistics": json.dumps(
                    [
                        {
                            "id": str(assistant[0]),
                            "name": assistant[1],
                            "number_of_conversations": assistant[2],
                        }
                        for assistant in assistant_statistics
                    ]
                ),
                "conversations_statistics": json.dumps(
                    [
                        {
                            "id": str(conversation.id),
                            "average_session_chat_time": conversation.average_session_chat_time,
                            "average_user_messages": conversation.average_user_messages,
                        }
                        for conversation in conversations
                    ]
                ),
            }
        ]
    )

    conversation_names = [
        conversation.name or conversation.id for conversation in conversations
    ]

    conversation_contents = [
        json.dumps(
            [
                {
                    "sender_type": m.sender_type,
                    "content": m.content,
                }
                for m in message
            ]
        )
        for message in messages
    ]

    conversation_df = pd.DataFrame(
        {
            "conversation_name": conversation_names,
            "conversation_content": conversation_contents,
        }
    )

    file_conversation_name = (
        Path(DOWNLOAD_FOLDER) / f"conversation_{current_user.id}.xlsx"
    )

    conversation_df.to_excel(file_conversation_name, index=False)

    file_name = Path(DOWNLOAD_FOLDER) / f"dashboard_{current_user.id}.xlsx"

    df.to_excel(file_name, index=False)

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
                name=assistant[1],
                number_of_conversations=assistant[2],
            )
            for assistant in assistant_statistics
        ],
        average_assistant_response_time=round(average_assistant_response_time, 2),
        knowledge_base_statistics=[
            KnowledgeBaseStaticsResponse(
                id=knowledge_base[0],
                name=knowledge_base[1],
                total_user_messages=knowledge_base[2],
            )
            for knowledge_base in knowledge_base_statistics
        ],
        file_name=file_name.stem,
        file_conversation_name=file_conversation_name.stem,
    )


@dashboard_router.get(
    "/export/{file_name}", tags=["download"], status_code=status.HTTP_200_OK
)
def download_file(
    file_name: str,
    current_user: Annotated[Users, Depends(get_current_user)],
):
    # Check if user has permission to download file
    user_id = file_name.split("_")[-1]

    if str(current_user.id) != user_id:
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={"error": "You do not have permission to download this file"},
        )

    file_path = Path(DOWNLOAD_FOLDER) / (file_name + ".xlsx")
    if file_path.exists():
        return FileResponse(
            file_path, filename=file_name, status_code=status.HTTP_200_OK
        )
    else:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND, content={"error": "File not found"}
        )


@dashboard_router.get("/wordcloud/kb/{knowledge_base_id}")
async def get_wordcloud_by_kb(
    knowledge_base_id: UUID,
    is_user: bool,
    current_user: Annotated[Users, Depends(get_current_user)],
    db_session: SessionDeps,
) -> JSONResponse:
    sender_type = SenderType.USER if is_user else SenderType.ASSISTANT

    knowledge_base = db_session.exec(
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

    text = db_session.exec(
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

    if not text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Empty Knowledge Base",
        )

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
    db_session: SessionDeps,
) -> JSONResponse:
    sender_type = SenderType.USER if is_user else SenderType.ASSISTANT

    assistant = db_session.exec(
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

    text = db_session.exec(
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
    db_session: SessionDeps,
) -> JSONResponse:
    sender_type = SenderType.USER if is_user else SenderType.ASSISTANT
    conversation = db_session.exec(
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

    text = db_session.exec(
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
    wordcloud = WordCloud(width=800, height=400, max_words=1000).generate(content)
    image_path = (
        Path(DOWNLOAD_FOLDER)
        / f"{str(conversation_id).replace('-', '_')}_{str(uuid.uuid4())}.png"
    )
    wordcloud.to_file(str(image_path))

    return FileResponse(
        path=image_path, filename=image_path.name, media_type="image/jpeg"
    )


@dashboard_router.get("/kbs", response_model=list[GetSourceReponse])
async def get_all_knowledge_bases(
    current_user: Annotated[Users, Depends(get_current_user)],
    db_session: SessionDeps,
):
    knowledge_bases = db_session.exec(
        select(KnowledgeBases)
        .where(KnowledgeBases.user_id == current_user.id)
        .order_by(desc(KnowledgeBases.updated_at))
    ).all()

    return knowledge_bases


@dashboard_router.get("/assistants", response_model=list[GetSourceReponse])
async def get_all_assistants(
    current_user: Annotated[Users, Depends(get_current_user)],
    db_session: SessionDeps,
):
    assistants = db_session.exec(
        select(Assistants)
        .where(Assistants.user_id == current_user.id)
        .order_by(desc(Assistants.updated_at))
    ).all()

    return assistants


@dashboard_router.get("/conversations", response_model=list[GetSourceReponse])
async def get_all_conversations(
    current_user: Annotated[Users, Depends(get_current_user)],
    db_session: SessionDeps,
):
    conversations = db_session.exec(
        select(Conversations)
        .where(Conversations.user_id == current_user.id)
        .order_by(desc(Conversations.updated_at))
    ).all()

    return [
        GetSourceReponse(id=conversation.id, name=conversation.name or conversation.id)
        for conversation in conversations
    ]
