import os
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from src.database.manager import DatabaseManager
from src.database.models import Assistant, Conversation, Message
from src.dependencies import get_db_manager
from src.agents.base import ChatAssistant
from api.models.assistant import (
    AssistantCreate, 
    AssistantResponse, 
    ChatMessage, 
    ChatResponse, 
    ConversationResponse,
    MessageResponse
)
from typing import List, Dict, Optional, Generator, AsyncGenerator


class AssistantService:
    def __init__(self, db_manager: DatabaseManager = Depends(get_db_manager)):
        self.db_manager = db_manager

    def create_assistant(self, user_id: int, assistant_data: AssistantCreate) -> AssistantResponse:

        with self.db_manager.Session() as session:
            print(assistant_data.systemprompt)
            new_assistant = Assistant(
                user_id=user_id, 
                name=assistant_data.name, 
                description=assistant_data.description,
                systemprompt=assistant_data.systemprompt,
                knowledge_base_id=assistant_data.knowledge_base_id, 
                configuration=assistant_data.configuration
            )
            
            session.add(new_assistant)
            session.commit()
            session.refresh(new_assistant)

            return AssistantResponse.model_validate(new_assistant)

    def delete_assistant(self, assistant_id: int, user_id: int) -> bool:
        return self.db_manager.delete_assistant(assistant_id, user_id)


    def get_all_assistants(self, user_id: int) -> List[AssistantResponse]:
        try:
            with self.db_manager.Session() as session:
                assistants = session.query(Assistant).filter_by(user_id=user_id).all()
                return [AssistantResponse.model_validate(assistant) for assistant in assistants]
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"An error occurred while fetching assistants: {str(e)}")

    def get_assistant(self, assistant_id: int, user_id: int) -> Optional[AssistantResponse]:
        try:
            with self.db_manager.Session() as session:
                assistant = session.query(Assistant).filter_by(id=assistant_id, user_id=user_id).first()
                if not assistant:
                    return None
                return AssistantResponse.model_validate(assistant)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"An error occurred while fetching assistant: {str(e)}")

    def create_conversation(self, user_id: int, assistant_id: str) -> ConversationResponse:
        try:
            with self.db_manager.Session() as session:
                assistant = session.query(Assistant).filter_by(id=assistant_id, user_id=user_id).first()
                if not assistant:
                    raise HTTPException(status_code=404, detail="Assistant not found")
                
                new_conversation = Conversation(
                    user_id=user_id,
                    assistant_id=assistant_id
                )
                session.add(new_conversation)
                session.commit()
                session.refresh(new_conversation)
                return ConversationResponse.model_validate(new_conversation)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"An error occurred while creating the conversation: {str(e)}")

    def get_assistant_conversations(self, assistant_id: int, user_id: int) -> Optional[List[ConversationResponse]]:
        try:
            with self.db_manager.Session() as session:
                assistant = session.query(Assistant).filter_by(id=assistant_id, user_id=user_id).first()
                if not assistant:
                    return None
                
                conversations = session.query(Conversation).filter_by(assistant_id=assistant_id).all()
                return [ConversationResponse.model_validate(conversation) for conversation in conversations]
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"An error occurred while fetching conversations: {str(e)}")

    def chat_with_assistant(self, conversation_id: int, user_id: int, message: ChatMessage) -> ChatResponse:
        try:
            with self.db_manager.Session() as session:
                conversation = session.query(Conversation).filter_by(id=conversation_id, user_id=user_id).first()
                if not conversation:
                    raise HTTPException(status_code=404, detail="Conversation not found")
                
                # Fetch message history
                message_history = self._get_message_history(session, conversation_id)
                
                # Save user message
                user_message = Message(
                    conversation_id=conversation_id,
                    sender_type="user",
                    content=message.content
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
                    "embedding_service": "openai", #TODO: Let user choose embedding model,
                    "embedding_model_name": "text-embedding-3-small",
                    "collection_name": f"kb_{assistant.knowledge_base_id}",
                    "conversation_id": conversation_id
                }
                
                assistant_instance = ChatAssistant(assistant_config)
                response = assistant_instance.on_message(message.content, message_history)
                
                # Save assistant message
                assistant_message = Message(
                    conversation_id=conversation_id,
                    sender_type="assistant",
                    content=response
                )
                session.add(assistant_message)
                
                session.commit()
                
                return ChatResponse(assistant_message=response)
        
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"An error occurred during the chat: {str(e)}")
            
            
    def stream_chat_with_assistant(self, conversation_id: int, user_id: int, message: ChatMessage) -> Generator[str, None, None]:
        with self.db_manager.Session() as session:
            conversation = session.query(Conversation).filter_by(id=conversation_id, user_id=user_id).first()
            if not conversation:
                raise HTTPException(status_code=404, detail="Conversation not found")
            
            message_history = self._get_message_history(session, conversation_id)
            
            user_message = Message(
                conversation_id=conversation_id,
                sender_type="user",
                content=message.content
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
                "conversation_id": conversation_id
            }
            
            assistant_instance = ChatAssistant(assistant_config)
            
            full_response = ""
            for chunk in assistant_instance.stream_chat(message.content, message_history):
                full_response += chunk
                yield chunk
            
            assistant_message = Message(
                conversation_id=conversation_id,
                sender_type="assistant",
                content=full_response
            )
            session.add(assistant_message)
            session.commit()
            
    async def astream_chat_with_assistant(self, conversation_id: int, user_id: int, message: ChatMessage):
        with self.db_manager.Session() as session:
            conversation = session.query(Conversation).filter_by(id=conversation_id, user_id=user_id).first()
            if not conversation:
                raise HTTPException(status_code=404, detail="Conversation not found")
            
            message_history = self._get_message_history(session, conversation_id)
            
            user_message = Message(
                conversation_id=conversation_id,
                sender_type="user",
                content=message.content
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
                "conversation_id": conversation_id
            }
            
            assistant_instance = ChatAssistant(assistant_config)
            
            full_response = ""
            response = await assistant_instance.astream_chat(message.content, message_history)

            async for chunk in response.async_response_gen():
                full_response += chunk
                yield chunk
            
            assistant_message = Message(
                conversation_id=conversation_id,
                sender_type="assistant",
                content=full_response
            )
            session.add(assistant_message)
            session.commit()
        
    def _get_message_history(self, session: Session, conversation_id: int) -> List[Dict[str, str]]:
        messages = session.query(Message).filter_by(conversation_id=conversation_id).order_by(Message.created_at).all()
        return [{"content": msg.content, "role": msg.sender_type} for msg in messages]

    def get_conversation_history(self, conversation_id: int, user_id: int) -> List[MessageResponse]:
        try:
            with self.db_manager.Session() as session:
                conversation = session.query(Conversation).filter_by(id=conversation_id, user_id=user_id).first()
                
                if not conversation:
                    raise HTTPException(status_code=404, detail="Conversation not found")
                
                messages = session.query(Message).filter_by(conversation_id=conversation_id).order_by(Message.created_at).all()
                return [MessageResponse.model_validate(message) for message in messages]
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"An error occurred while fetching conversation history: {str(e)}")