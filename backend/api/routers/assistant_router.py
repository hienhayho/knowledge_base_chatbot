import time
import json
import pandas as pd

from uuid import UUID
from src.database import is_valid_uuid
from typing import Annotated
from sqlmodel import Session, select
from api.routers.user_router import get_current_user
from api.models import (
    AssistantCreate,
    AssistantResponse,
    ChatMessage,
    AssistantWithTotalCost,
    AsistantUpdatePhraseRequest,
    ConversationRenameRequest,
    AssistantUpdateToolsRequest,
)
from .user_router import decode_user_token
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    WebSocket,
    WebSocketDisconnect,
)
from src.database import (
    Assistants,
    Messages,
    get_session,
    Users,
    KnowledgeBases,
    Conversations,
    WsManager,
    MediaType,
    EndStatus,
    get_ws_manager,
    DatabaseManager,
    get_db_manager,
)
from src.constants import DOWNLOAD_FOLDER
from src.utils import get_formatted_logger
from api.services import AssistantService
from fastapi.responses import JSONResponse, FileResponse

logger = get_formatted_logger(__file__)

assistant_router = APIRouter()


@assistant_router.post("/", response_model=AssistantResponse)
async def create_assistant(
    assistant: AssistantCreate,
    current_user: Annotated[Users, Depends(get_current_user)],
    db_session: Annotated[Session, Depends(get_session)],
):
    """
    Create a new assistant for the given user
    """
    with db_session as session:
        if not is_valid_uuid(assistant.knowledge_base_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid knowledge base id",
            )

        query = select(KnowledgeBases).where(
            KnowledgeBases.id == assistant.knowledge_base_id
        )

        knowledge_base = session.exec(query).first()
        if not knowledge_base:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge base not found"
            )

        if knowledge_base.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not authorized to access this knowledge base",
            )

        new_assistant = Assistants(
            name=assistant.name,
            description=assistant.description,
            knowledge_base_id=assistant.knowledge_base_id,
            configuration=assistant.configuration,
            user_id=current_user.id,
            agent_backstory=assistant.agent_backstory,
            instruct_prompt=assistant.instruct_prompt,
        )
        session.add(new_assistant)
        session.commit()
        session.refresh(new_assistant)
        session.close()

        return new_assistant


@assistant_router.get("/", response_model=list[AssistantResponse])
async def get_all_assistants(
    current_user: Annotated[Users, Depends(get_current_user)],
    db_session: Annotated[Session, Depends(get_session)],
):
    with db_session as session:
        query = select(Assistants).where(Assistants.user_id == current_user.id)
        assistants = session.exec(query).all()

        session.close()

        return assistants


@assistant_router.get("/{assistant_id}", response_model=AssistantResponse)
async def get_assistant(
    assistant_id: str,
    current_user: Annotated[Users, Depends(get_current_user)],
    db_session: Annotated[Session, Depends(get_session)],
):
    with db_session as session:
        if not is_valid_uuid(assistant_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid assistant id"
            )

        query = select(Assistants).where(
            Assistants.id == assistant_id, Assistants.user_id == current_user.id
        )
        assistant = session.exec(query).first()
        if not assistant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Assistant not found"
            )

        session.close()

        return assistant


@assistant_router.post("/{assistant_id}/update", response_model=AssistantResponse)
async def update_assistant(
    assistant_id: str,
    assistant_phrases: AsistantUpdatePhraseRequest,
    current_user: Annotated[Users, Depends(get_current_user)],
    db_session: Annotated[Session, Depends(get_session)],
):
    with db_session as session:
        if not is_valid_uuid(assistant_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid assistant id"
            )

        query = select(Assistants).where(
            Assistants.id == assistant_id, Assistants.user_id == current_user.id
        )
        assistant = session.exec(query).first()
        if not assistant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Assistant not found"
            )

        assistant.instruct_prompt = assistant_phrases.instruct_prompt
        assistant.agent_backstory = assistant_phrases.agent_backstory

        session.commit()
        session.refresh(assistant)

        return assistant


@assistant_router.post("/{assistant_id}/tools", response_model=AssistantResponse)
async def update_assistant_tool(
    assistant_id: str,
    assistant_phrases: AssistantUpdateToolsRequest,
    current_user: Annotated[Users, Depends(get_current_user)],
    db_session: Annotated[Session, Depends(get_session)],
):
    with db_session as session:
        if not is_valid_uuid(assistant_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid assistant id"
            )

        query = select(Assistants).where(
            Assistants.id == assistant_id, Assistants.user_id == current_user.id
        )
        assistant = session.exec(query).first()
        if not assistant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Assistant not found"
            )

        tool_configurations = {
            tool.name: tool.description for tool in assistant_phrases.tools
        }

        assistant.tools = tool_configurations

        session.commit()
        session.refresh(assistant)

        return assistant


@assistant_router.get(
    "/{assistant_id}/total_cost", response_model=AssistantWithTotalCost
)
async def get_assistant_with_total_cost(
    assistant_id: str,
    current_user: Annotated[Users, Depends(get_current_user)],
    db_session: Annotated[Session, Depends(get_session)],
):
    with db_session as session:
        if not is_valid_uuid(assistant_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid assistant id"
            )

        query = select(Assistants).where(
            Assistants.id == assistant_id, Assistants.user_id == current_user.id
        )
        assistant = session.exec(query).first()

        conversation_ids = session.exec(
            select(Conversations.id).where(Conversations.assistant_id == assistant_id)
        ).all()

        conversations = [
            session.exec(select(Conversations).where(Conversations.id == c)).first()
            for c in conversation_ids
        ]
        messages = [
            session.exec(select(Messages).where(Messages.conversation_id == c)).all()
            for c in conversation_ids
        ]
        if not assistant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Assistant not found"
            )

        session.close()

        return AssistantWithTotalCost(
            id=assistant.id,
            user_id=assistant.user_id,
            name=assistant.name,
            description=assistant.description,
            knowledge_base_id=assistant.knowledge_base_id,
            configuration=assistant.configuration,
            created_at=assistant.created_at,
            updated_at=assistant.updated_at,
            total_cost=assistant.total_cost(
                conversations=conversations, messages=messages
            ),
        )


@assistant_router.post("/{assistant_id}/conversations")
async def create_conversation(
    assistant_id: str,
    current_user: Annotated[Users, Depends(get_current_user)],
    db_session: Annotated[Session, Depends(get_session)],
):
    with db_session as session:
        if not is_valid_uuid(assistant_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid assistant id"
            )

        query = select(Assistants).where(
            Assistants.id == assistant_id, Assistants.user_id == current_user.id
        )
        assistant = session.exec(query).first()
        if not assistant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Assistant not found"
            )

        new_conversation = Conversations(
            assistant_id=assistant_id, user_id=current_user.id
        )
        session.add(new_conversation)
        session.commit()
        return new_conversation


@assistant_router.get("/{assistant_id}/conversations")
async def get_assistant_conversations(
    assistant_id: str,
    current_user: Annotated[Users, Depends(get_current_user)],
    db_session: Annotated[Session, Depends(get_session)],
):
    with db_session as session:
        if not is_valid_uuid(assistant_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid assistant id"
            )

        query = select(Assistants).where(
            Assistants.id == assistant_id, Assistants.user_id == current_user.id
        )

        assistant = session.exec(query).first()
        if not assistant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Assistant not found"
            )

        query = select(Conversations).where(Conversations.assistant_id == assistant.id)
        conversations = session.exec(query).all()
        return conversations


@assistant_router.delete("/{assistant_id}/conversations/{conversation_id}")
async def delete_conversation(
    assistant_id: str,
    conversation_id: str,
    current_user: Annotated[Users, Depends(get_current_user)],
    db_session: Annotated[Session, Depends(get_session)],
    db_manager: Annotated[DatabaseManager, Depends(get_db_manager)],
):
    with db_session as session:
        if not is_valid_uuid(assistant_id) or not is_valid_uuid(conversation_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid assistant or conversation id",
            )

        assistant = session.exec(
            select(Assistants).where(
                Assistants.id == assistant_id, Assistants.user_id == current_user.id
            )
        ).first()

        if not assistant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Assistant not found"
            )

        db_manager.delete_conversation(
            conversation_id=conversation_id,
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"message": "Conversation deleted successfully"},
        )


@assistant_router.get("/{assistant_id}/export_conversations")
async def export_conversations(
    assistant_id: UUID,
    current_user: Annotated[Users, Depends(get_current_user)],
    db_session: Annotated[Session, Depends(get_session)],
):
    with db_session as session:
        conversations = session.exec(
            select(Conversations).where(
                Conversations.assistant_id == assistant_id,
                Conversations.user_id == current_user.id,
            )
        ).all()

        conversations_name = [
            conversation.name or conversation.id for conversation in conversations
        ]

        conversations_content = [
            session.exec(
                select(Messages)
                .where(Messages.conversation_id == conversation.id)
                .order_by(Messages.created_at)
            ).all()
            for conversation in conversations
        ]

        conversations_string = [
            json.dumps(
                [
                    {
                        "sender": message.sender_type,
                        "content": message.content,
                    }
                    for message in conversation
                ]
            )
            for conversation in conversations_content
        ]

        df = pd.DataFrame(
            {
                "conversation_name": conversations_name,
                "conversation_content": conversations_string,
            }
        )

        # Save to excel
        df.to_excel(DOWNLOAD_FOLDER / f"{assistant_id}.xlsx", index=False)

        return FileResponse(
            DOWNLOAD_FOLDER / f"{assistant_id}.xlsx",
            filename=f"{assistant_id}.xlsx",
            status_code=200,
        )


@assistant_router.get("/{assistant_id}/export/{conversation_id}")
async def export_conversation(
    assistant_id: UUID,
    conversation_id: UUID,
    current_user: Annotated[Users, Depends(get_current_user)],
    assistant_service: AssistantService = Depends(),
):
    conversation = [
        {
            "sender": conv.sender_type,
            "content": conv.content,
        }
        for conv in assistant_service.get_conversation_history(
            assistant_id, conversation_id, current_user.id
        )
    ]

    with open(DOWNLOAD_FOLDER / f"{conversation_id}.json", "w") as f:
        json.dump(conversation, f, indent=4)

    return FileResponse(
        DOWNLOAD_FOLDER / f"{conversation_id}.json",
        filename=f"{conversation_id}.json",
        status_code=200,
    )


@assistant_router.get("/{assistant_id}/conversations/{conversation_id}/history")
async def get_conversation_history(
    assistant_id: UUID,
    conversation_id: UUID,
    current_user: Annotated[Users, Depends(get_current_user)],
    assistant_service: AssistantService = Depends(),
):
    return assistant_service.get_conversation_history(
        assistant_id, conversation_id, current_user.id
    )


@assistant_router.patch("/{assistant_id}/conversations/{conversation_id}/rename")
async def rename_conversation_name(
    assistant_id: UUID,
    conversation_id: UUID,
    conversation_rename_body: ConversationRenameRequest,
    current_user: Annotated[Users, Depends(get_current_user)],
    db_session: Annotated[Session, Depends(get_session)],
):
    with db_session as session:
        query = select(Conversations).where(
            Conversations.id == conversation_id,
            Conversations.assistant_id == assistant_id,
        )
        conversation = session.exec(query).first()
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found"
            )
        if conversation.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not authorized to rename this conversation",
            )

        conversation.name = conversation_rename_body.name
        session.commit()

        return JSONResponse(
            status_code=status.HTTP_200_OK, content={"message": "Conversation renamed"}
        )


@assistant_router.delete("/{assistant_id}")
async def delete_assistant(
    assistant_id: str,
    current_user: Annotated[Users, Depends(get_current_user)],
    db_session: Annotated[Session, Depends(get_session)],
    db_manager: Annotated[DatabaseManager, Depends(get_db_manager)],
):
    with db_session as session:
        if not is_valid_uuid(assistant_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid assistant id"
            )

        assistant = session.exec(
            select(Assistants).where(
                Assistants.id == assistant_id, Assistants.user_id == current_user.id
            )
        ).first()

        if not assistant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Assistant not found"
            )

        db_manager.delete_assistant(assistant_id)

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"message": "Assistant deleted successfully"},
        )


@assistant_router.websocket(
    "/{assistant_id}/conversations/{conversation_id}/{token}/ws"
)
async def websocket_endpoint(
    websocket: WebSocket,
    assistant_id: UUID,
    conversation_id: UUID,
    token: str,
    db_session: Annotated[Session, Depends(get_session)],
    ws_manager: Annotated[WsManager, Depends(get_ws_manager)],
    assistant_service: Annotated[AssistantService, Depends()],
):
    assistant_id = str(assistant_id)
    conversation_id = str(conversation_id)

    await ws_manager.connect(conversation_id, websocket)
    current_user = await decode_user_token(token, db_session)

    session_start_time = time.time()
    user_has_chat = False
    session_message_count = 0
    try:
        while True:
            start_time = time.time()
            data = await websocket.receive_json()

            user_has_chat = True
            session_message_count += 1

            # Send acknowledgement of received message
            await ws_manager.send_status(conversation_id, "message_received")

            # Process the incoming message
            message = ChatMessage(content=data["content"])

            try:
                async for chunk in assistant_service.astream_chat_with_assistant(
                    conversation_id, current_user.id, message, start_time
                ):
                    # Assume chunk is a string. If it's a different structure, adjust accordingly.
                    await ws_manager.send_text_message(
                        conversation_id,
                        chunk,
                        sender_type="assistant",
                        extra_metadata={"assistant_id": assistant_id},
                    )

                # Send end message for successful completion
                await ws_manager.send_end_message(
                    conversation_id,
                    MediaType.TEXT,
                    EndStatus.COMPLETE,
                    {"assistant_id": assistant_id},
                )

            except Exception as e:
                print(e)
                # Handle any errors during message processing
                error_message = f"Error processing message: {str(e)}"
                await ws_manager.send_error(conversation_id, error_message)
                await ws_manager.send_end_message(
                    conversation_id,
                    MediaType.TEXT,
                    EndStatus.ERROR,
                    {"error_message": error_message, "assistant_id": assistant_id},
                )

    except WebSocketDisconnect:
        if user_has_chat:
            with db_session as session:
                conversation = session.exec(
                    select(Conversations).where(Conversations.id == conversation_id)
                ).first()
                if conversation:
                    conversation.session_chat_time = conversation.session_chat_time + (
                        time.time() - session_start_time
                    )

                    conversation.user_messages += session_message_count

                    conversation.number_of_sessions += 1

                    session.add(conversation)
                    session.commit()

                else:
                    logger.error(
                        f"Conversation {conversation_id} not found while updating average chat time"
                    )

        # Handle WebSocket disconnect
        ws_manager.disconnect(conversation_id)
        # You might want to log this disconnect or perform any cleanup
        logger.info(f"WebSocket disconnected for conversation {conversation_id}")

    except Exception as e:
        print(e)
        # Handle any other unexpected errors
        error_message = f"Unexpected error in WebSocket connection: {str(e)}"
        await ws_manager.send_error(conversation_id, error_message)
        await ws_manager.send_end_message(
            conversation_id,
            MediaType.TEXT,
            EndStatus.ERROR,
            {"error_message": error_message, "assistant_id": assistant_id},
        )
        ws_manager.disconnect(conversation_id)
