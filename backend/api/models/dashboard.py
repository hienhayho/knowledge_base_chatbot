from uuid import UUID
from pydantic import BaseModel, Field


class ConversationStaticsResponse(BaseModel):
    id: UUID
    average_session_chat_time: float
    average_user_messages: int


class KnowledgeBaseStaticsResponse(BaseModel):
    id: UUID
    name: str
    total_user_messages: int


class AssistantStaticsResponse(BaseModel):
    id: UUID
    name: str
    number_of_conversations: int


class DashboardStaticsResponse(BaseModel):
    total_conversations: int = Field(
        ..., description="Total number of conversations each user"
    )

    assistant_statistics: list[AssistantStaticsResponse] = Field(
        ..., description="List of assistant statistics for each user"
    )

    conversations_statistics: list[ConversationStaticsResponse] = Field(
        ..., description="List of conversation statistics for each user"
    )

    average_assistant_response_time: float = Field(
        ...,
        description="Average response time of the assistant among all knowledge bases of each user",
    )

    knowledge_base_statistics: list[KnowledgeBaseStaticsResponse] = Field(
        ..., description="List of knowledge base statistics for each user"
    )
    file_name: str
    file_conversation_name: str


class GetSourceReponse(BaseModel):
    id: UUID
    name: str | UUID
