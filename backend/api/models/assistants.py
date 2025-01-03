from uuid import UUID
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, ConfigDict


class AssistantCreate(BaseModel):
    name: str
    description: Optional[str] = None
    instruct_prompt: str
    agent_backstory: Optional[str] = None
    knowledge_base_id: str
    configuration: Dict[str, Any]


class AssistantResponse(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    description: Optional[str]
    instruct_prompt: str
    agent_backstory: str
    tools: Dict[str, Dict[str, Any]]
    knowledge_base_id: UUID
    configuration: Dict[str, str]
    created_at: datetime
    updated_at: datetime
    exist_tools: list[str]
    agent_type: str

    model_config = ConfigDict(from_attributes=True)


class AsistantUpdatePhraseRequest(BaseModel):
    instruct_prompt: str
    agent_backstory: str = None
    agent_type: str = None

    model_config = ConfigDict(from_attributes=True)


class ToolUpdateRequest(BaseModel):
    name: str
    description: str
    return_as_answer: bool


class AssistantUpdateToolsRequest(BaseModel):
    tools: list[ToolUpdateRequest]


class AssistantWithTotalCost(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    description: Optional[str]
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


class ConversationRenameRequest(BaseModel):
    name: str


class ChatMessage(BaseModel):
    content: str


class ChatResponse(BaseModel):
    assistant_message: str
    created_at: datetime


class ChatMessageResponse(BaseModel):
    assistant_message: str
    type: str
    metadata: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None


class MessageResponse(BaseModel):
    id: UUID
    conversation_id: UUID
    sender_type: str
    content: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
