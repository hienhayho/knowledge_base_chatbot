import uuid
from uuid import UUID
from sqlmodel import Session, select
from typing import List, Dict, Generator
from fastapi import Depends, HTTPException
from langfuse.decorators import langfuse_context

from src.agents import ChatAssistant
from src.utils import get_cost_from_session_id
from src.database import get_session, Messages, Conversations
from api.models import (
    ChatMessage,
    ChatResponse,
    MessageResponse,
)
from src.constants import SenderType


class AssistantService:
    def __init__(self, db_session: Session = Depends(get_session)):
        self.db_session = db_session

    def chat_with_assistant(
        self, conversation_id: UUID, user_id: int, message: ChatMessage
    ) -> ChatResponse:
        try:
            with self.db_session as session:
                query = select(Conversations).filter_by(
                    id=conversation_id, user_id=user_id
                )

                conversation = session.exec(query).first()

                if not conversation:
                    raise HTTPException(
                        status_code=404, detail="Conversation not found"
                    )

                # Fetch message history
                message_history = self._get_message_history(session, conversation_id)

                # Save user message
                user_message = Messages(
                    conversation_id=conversation_id,
                    sender_type=SenderType.USER,
                    content=message.content,
                )
                session.add(user_message)
                session.flush()  # Flush to get the ID of the new message

                # Here we assume that the Assistant class has an on_message method
                # In a real implementation, you might need to instantiate the assistant with its configuration
                assistant = conversation.assistant

                configuration = assistant.configuration

                assistant_config = {
                    "model": configuration["model"],
                    "service": configuration["service"],
                    "temperature": configuration["temperature"],
                    "embedding_service": "openai",  # TODO: Let user choose embedding model,
                    "embedding_model_name": "text-embedding-3-small",
                    "collection_name": f"{assistant.knowledge_base_id}",
                    "conversation_id": conversation_id,
                }

                assistant_instance = ChatAssistant(assistant_config)
                response = assistant_instance.on_message(
                    message.content, message_history
                )

                # Save assistant message
                assistant_message = Messages(
                    conversation_id=conversation_id,
                    sender_type=SenderType.ASSISTANT,
                    content=response,
                )
                session.add(assistant_message)

                session.commit()

                return ChatResponse(assistant_message=response)

        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"An error occurred during the chat: {str(e)}"
            )

    def stream_chat_with_assistant(
        self, conversation_id: int, user_id: int, message: ChatMessage
    ) -> Generator[str, None, None]:
        with self.db_manager.Session() as session:
            conversation = (
                session.query(Conversations)
                .filter_by(id=conversation_id, user_id=user_id)
                .first()
            )
            if not conversation:
                raise HTTPException(status_code=404, detail="Conversation not found")

            message_history = self._get_message_history(session, conversation_id)

            user_message = Messages(
                conversation_id=conversation_id,
                sender_type=SenderType.USER,
                content=message.content,
            )
            session.add(user_message)
            session.flush()

            assistant = conversation.assistant
            configuration = assistant.configuration

            assistant_config = {
                "model": configuration["model"],
                "service": configuration["service"],
                "temperature": configuration["temperature"],
                "embedding_service": "openai",
                "embedding_model_name": "text-embedding-3-small",
                "collection_name": f"kb_{assistant.knowledge_base_id}",
                "conversation_id": conversation_id,
            }

            assistant_instance = ChatAssistant(assistant_config)

            full_response = ""
            for chunk in assistant_instance.stream_chat(
                message.content, message_history
            ):
                full_response += chunk
                yield chunk

            assistant_message = Messages(
                conversation_id=conversation_id,
                sender_type=SenderType.ASSISTANT,
                content=full_response,
            )
            session.add(assistant_message)
            session.commit()

    async def astream_chat_with_assistant(
        self, conversation_id: UUID, user_id: UUID, message: ChatMessage
    ):
        with self.db_session as session:
            query = select(Conversations).where(
                Conversations.id == conversation_id,
                Conversations.user_id == user_id,
            )

            conversation = session.exec(query).first()

            is_contextual_rag = conversation.assistant.knowledge_base.is_contextual_rag
            assistant = conversation.assistant
            configuration = assistant.configuration

            if not conversation:
                raise HTTPException(status_code=404, detail="Conversation not found")

            message_history = self._get_message_history(conversation_id)

            user_message = Messages(
                conversation_id=conversation_id,
                sender_type=SenderType.USER,
                content=message.content,
            )
            session.add(user_message)
            session.flush()

            session_id = str(uuid.uuid4())
            assistant_config = {
                "model": configuration["model"],
                "service": configuration["service"],
                "temperature": configuration["temperature"],
                "embedding_service": "openai",
                "embedding_model_name": "text-embedding-3-small",
                "collection_name": f"{assistant.knowledge_base_id}",
                "session_id": session_id,
                "is_contextual_rag": is_contextual_rag,
            }

            assistant_instance = ChatAssistant(assistant_config)

            full_response = ""

            response = await assistant_instance.astream_chat(
                message.content, message_history, session_id=session_id
            )

            async for chunk in response.async_response_gen():
                full_response += chunk
                yield chunk

            langfuse_context.flush()

            assistant_message = Messages(
                id=session_id,
                conversation_id=conversation_id,
                sender_type=SenderType.ASSISTANT,
                content=full_response,
                cost=get_cost_from_session_id(session_id),
            )
            session.add(assistant_message)
            session.commit()

    def _get_message_history(self, conversation_id: UUID) -> List[Dict[str, str]]:
        with self.db_session as session:
            query = (
                select(Messages)
                .where(Messages.conversation_id == conversation_id)
                .order_by(Messages.created_at)
            )

            messages = session.exec(query).all()

            return [
                {"content": msg.content, "role": msg.sender_type} for msg in messages
            ]

    def get_conversation_history(
        self, conversation_id: int, user_id: int
    ) -> List[MessageResponse]:
        try:
            with self.db_session as session:
                query = select(Conversations).where(
                    Conversations.id == conversation_id,
                    Conversations.user_id == user_id,
                )

                conversation = session.exec(query).first()

                if not conversation:
                    raise HTTPException(
                        status_code=404, detail="Conversation not found"
                    )

                query = (
                    select(Messages)
                    .where(Messages.conversation_id == conversation_id)
                    .order_by(Messages.created_at)
                )

                messages = session.exec(query).all()

                return [MessageResponse.model_validate(message) for message in messages]
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"An error occurred while fetching conversation history: {str(e)}",
            )
