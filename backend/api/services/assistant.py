import time
import uuid
import copy

from uuid import UUID
from sqlmodel import Session, select
from langfuse.decorators import langfuse_context
from fastapi import Depends, HTTPException, status
from typing import List, Generator, Dict, Any, Union

from .chat_assistant_agent import ChatAssistant
from .output_parser import OutputParser, get_default_output_parser
from src.utils import get_cost_from_session_id
from src.database import (
    get_session,
    Messages,
    Conversations,
    Assistants,
    KnowledgeBases,
    get_db_manager,
    DatabaseManager,
)
from api.models import (
    ChatMessage,
    ChatResponse,
)
from src.settings import default_settings
from src.constants import SenderType, ChatAssistantConfig, MesssageHistory


class AssistantService:
    def __init__(
        self,
        db_session: Session = Depends(get_session),
        db_manager: DatabaseManager = Depends(get_db_manager),
        output_parser: OutputParser = Depends(get_default_output_parser),
    ):
        self.db_session = db_session
        self.db_manager = db_manager
        self.output_parser = output_parser

    def chat_with_assistant(
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

            file_product_path = self.db_manager.get_product_file_path(
                knowledge_base_id=kb.id
            )

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
                file_product_path=file_product_path,
            )

            assistant_instance = ChatAssistant(configuration=assistant_config)

            answer = assistant_instance.on_message(
                message.content, message_history, session_id=session_id
            )

            response = {
                "result": answer,
                "is_chat_false": False,
            }

            langfuse_context.flush()

            assistant_message = Messages(
                id=session_id,
                conversation_id=conversation_id,
                sender_type=SenderType.ASSISTANT,
                content=answer,
                response_time=time.time() - start_time,
                is_chat_false=response["is_chat_false"],
                cost=get_cost_from_session_id(session_id),
            )
            session.add(assistant_message)
            session.commit()

            return ChatResponse(
                assistant_message=answer,
            )

    async def achat_with_assistant(
        self,
        conversation_id: UUID,
        user_id: UUID,
        message: ChatMessage,
        start_time: float,
        use_parser: bool = False,
    ) -> Union[ChatResponse, Dict[str, Any]]:
        """
        Chat with assistant.

        Args:
            conversation_id (UUID): Conversation ID.
            user_id (UUID): User ID.
            message (ChatMessage): Chat message.
            start_time (float): Start time.
            use_parser (bool): Use output parser flag before returning to FE.

        Returns:
            Union[ChatResponse, Dict[str, Any]]: Chat response. When use_parser is True, it returns parsed json output.
        """

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

            file_product_path = self.db_manager.get_product_file_path(
                knowledge_base_id=kb.id
            )

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
                file_product_path=file_product_path,
            )

            assistant_instance = ChatAssistant(configuration=assistant_config)

            answer = await assistant_instance.aon_message(
                message.content, message_history, session_id=session_id
            )

            response = {
                "result": answer,
                "is_chat_false": False,
            }

            langfuse_context.flush()

            assistant_message = Messages(
                id=session_id,
                conversation_id=conversation_id,
                sender_type=SenderType.ASSISTANT,
                content=answer,
                response_time=time.time() - start_time,
                is_chat_false=response["is_chat_false"],
                cost=get_cost_from_session_id(session_id),
            )
            session.add(assistant_message)
            session.commit()

            if use_parser:
                result = self.output_parser._parse_output(answer)
                return result

            return ChatResponse(
                assistant_message=answer,
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

            file_product_path = self.db_manager.get_product_file_path(
                knowledge_base_id=kb.id
            )

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
                file_product_path=file_product_path,
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
