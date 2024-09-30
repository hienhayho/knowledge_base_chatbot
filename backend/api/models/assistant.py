from pydantic import BaseModel, ConfigDict
from typing import Optional, Dict
from datetime import datetime

class AssistantCreate(BaseModel):
    name: str
    description: Optional[str] = None
    systemprompt: Optional[str] = None
    knowledge_base_id: int
    configuration: Dict[str, str]

class AssistantResponse(BaseModel):
    id: int
    user_id: int
    name: str
    description: Optional[str]
    systemprompt: Optional[str]
    knowledge_base_id: int
    configuration: Dict[str, str]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ConversationResponse(BaseModel):
    id: int
    user_id: int
    assistant_id: int
    started_at: datetime
    ended_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)

class ChatMessage(BaseModel):
    content: str

class ChatResponse(BaseModel):
    assistant_message: str

class MessageResponse(BaseModel):
    id: int
    conversation_id: int
    sender_type: str
    content: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)