from uuid import UUID
from typing import Any
from datetime import datetime
from typing import Optional, Dict
from pydantic import BaseModel, ConfigDict


class AssistantCreate(BaseModel):
    name: str
    description: Optional[str] = None
    system_prompt: Optional[str] = None
    knowledge_base_id: str
    configuration: Dict[str, Any]


class AssistantResponse(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    description: Optional[str]
    system_prompt: Optional[str]
    knowledge_base_id: UUID
    configuration: Dict[str, str]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AssistantWithTotalCost(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    description: Optional[str]
    system_prompt: Optional[str]
    knowledge_base_id: UUID
    configuration: Dict[str, str]
    created_at: datetime
    updated_at: datetime
    total_cost: float

    model_config = ConfigDict(from_attributes=True)


class ConversationResponse(BaseModel):
    id: UUID
    user_id: UUID
    assistant_id: UUID
    started_at: datetime
    ended_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class ChatMessage(BaseModel):
    content: str


class ChatResponse(BaseModel):
    assistant_message: str


class MessageResponse(BaseModel):
    id: UUID
    conversation_id: UUID
    sender_type: str
    content: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
