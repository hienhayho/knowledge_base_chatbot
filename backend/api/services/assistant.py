import time
import uuid
import copy

from uuid import UUID
from typing import List, Generator
from sqlmodel import Session, select
from langfuse.decorators import langfuse_context
from fastapi import Depends, HTTPException, status

from .chat_assistant_agent import ChatAssistant
from src.utils import get_cost_from_session_id
from src.database import (
    get_session,
    Messages,
    Conversations,
    Assistants,
    KnowledgeBases,
)
from api.models import (
    ChatMessage,
    ChatResponse,
    MessageResponse,
)
from src.settings import default_settings
from src.constants import SenderType, ChatAssistantConfig, MesssageHistory


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
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Conversation not found",
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
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"An error occurred during the chat: {str(e)}",
            )

    def stream_chat_with_assistant(
        self, conversation_id: int, user_id: int, message: ChatMessage
    ) -> Generator[str, None, None]:
        with self.db_session as session:
            conversation = (
                session.query(Conversations)
                .filter_by(id=conversation_id, user_id=user_id)
                .first()
            )
            if not conversation:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Conversation not found",
                )

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

            assistant_config = ChatAssistantConfig(
                model=configuration["model"],
                service=configuration["service"],
                temperature=configuration["temperature"],
                embedding_service="openai",
                embedding_model_name="text-embedding-3-small",
                collection_name=f"{assistant.knowledge_base_id}",
            )

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
        self,
        conversation_id: UUID,
        user_id: UUID,
        message: ChatMessage,
        start_time: float,
    ):
        with self.db_session as session:
            query = select(Conversations).where(
                Conversations.id == conversation_id,
                Conversations.user_id == user_id,
            )

            conversation = session.exec(query).first()

            is_contextual_rag = True
            assistant = session.exec(
                select(Assistants).where(Assistants.id == conversation.assistant_id)
            ).first()
            configuration = assistant.configuration

            if not conversation:
                raise HTTPException(status_code=404, detail="Conversation not found")

            kb = session.exec(
                select(KnowledgeBases).where(
                    KnowledgeBases.id == assistant.knowledge_base_id
                )
            ).first()

            kb_ids = copy.deepcopy(kb.parents)
            kb_ids.append(kb.id)

            message_history = self._get_message_history(conversation_id)

            user_message = Messages(
                conversation_id=conversation_id,
                sender_type=SenderType.USER,
                content=message.content,
            )
            session.add(user_message)
            session.flush()

            session_id = str(uuid.uuid4())

            assistant_config = ChatAssistantConfig(
                model=configuration["model"],
                conversation_id=conversation_id,
                service=configuration["service"],
                temperature=configuration["temperature"],
                embedding_service="openai",
                embedding_model_name="text-embedding-3-small",
                collection_name=default_settings.global_vector_db_collection_name,
                kb_ids=kb_ids,
                session_id=session_id,
                tools=assistant.tools,
                agent_backstory=assistant.agent_backstory,
                is_contextual_rag=is_contextual_rag,
                instruct_prompt=assistant.instruct_prompt,
            )

            assistant_instance = ChatAssistant(configuration=assistant_config)

            response_time = None
            full_response = ""

            answer = assistant_instance.on_message(
                message.content, message_history, session_id=session_id
            )

            response = {
                "result": answer,
                "is_chat_false": False,
            }

            # response = repair_json(response, return_objects=True)

            if not response:
                response["result"] = "Something went wrong. Please try again."
                response["is_chat_false"] = False

            for chunk in response["result"].strip().split(" "):
                if response_time is None:
                    response_time = time.time() - start_time

                full_response += chunk + " "
                yield chunk + " "

            langfuse_context.flush()

            assistant_message = Messages(
                id=session_id,
                conversation_id=conversation_id,
                sender_type=SenderType.ASSISTANT,
                content=full_response,
                response_time=response_time,
                is_chat_false=response["is_chat_false"],
                cost=get_cost_from_session_id(session_id),
            )
            session.add(assistant_message)
            session.commit()

    def _get_message_history(self, conversation_id: UUID) -> List[MesssageHistory]:
        with self.db_session as session:
            query = (
                select(Messages)
                .where(Messages.conversation_id == conversation_id)
                .order_by(Messages.created_at)
            )

            messages = session.exec(query).all()

            return [
                MesssageHistory(content=msg.content, role=msg.sender_type)
                for msg in messages
            ]

    def get_conversation_history(
        self, assistant_id: UUID, conversation_id: UUID, user_id: UUID
    ) -> List[MessageResponse]:
        try:
            with self.db_session as session:
                query = select(Conversations).where(
                    Conversations.assistant_id == assistant_id,
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
