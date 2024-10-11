import sys
from uuid import UUID
from pathlib import Path
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict

sys.path.append(str(Path(__file__).parent.parent.parent))

from api.models import UserResponse
from src.constants import FileStatus
from src.database import KnowledgeBases


class KnowledgeBaseRequest(BaseModel):
    name: str = Field(
        ...,
        title="Name of the Knowledge Base",
        description="Name of the Knowledge Base",
    )
    description: str = Field(
        default="No description",
        title="Description of the Knowledge Base",
        description="Description of the Knowledge Base",
    )


class MergeKnowledgeBasesRequest(BaseModel):
    knowledge_base_ids: list[UUID] = Field(
        ...,
        title="List of Knowledge Base IDs",
        description="List of Knowledge Base IDs to be merged",
    )
    name: str = Field(
        default="Merged Knowledge Base",
        title="Name of the merged Knowledge Base",
        description="Name of the merged Knowledge Base",
    )
    description: str = Field(
        default="No description",
        title="Description of the merged Knowledge Base",
        description="Description of the merged Knowledge Base",
    )


class KnowledgeBaseResponse(BaseModel):
    id: UUID = Field(
        ...,
        title="Knowledge Base ID",
        description="Knowledge Base ID",
    )
    name: str = Field(
        ...,
        title="Name of the Knowledge Base",
        description="Name of the Knowledge Base",
    )
    description: str = Field(
        default="No description",
        title="Description of the Knowledge Base",
        description="Description of the Knowledge Base",
    )
    created_at: datetime = Field(
        ...,
        title="Created At time",
        description="Created At time",
    )
    updated_at: datetime = Field(
        ...,
        title="Updated At time",
        description="Updated At time",
    )
    user: UserResponse = Field(
        ...,
        title="Owner of the Knowledge Base",
        description="Owner of the Knowledge Base",
    )


class UploadFileResponse(BaseModel):
    doc_id: UUID = Field(
        ...,
        title="Document ID",
        description="Document ID",
    )
    file_name: str = Field(
        ...,
        title="File Name",
        description="File Name",
    )
    file_type: str = Field(
        ...,
        title="File extension",
        description="File extension",
    )
    status: FileStatus = Field(
        ...,
        title="Status of the Document",
        description="Status of the Document",
    )
    knowledge_base: KnowledgeBases = Field(
        ...,
        title="Knowledge Base",
        description="Knowledge Base",
    )


class GetDocumentStatusReponse(BaseModel):
    doc_id: UUID = Field(
        ...,
        title="Document ID",
        description="Document ID",
    )
    status: FileStatus = Field(
        ...,
        title="Status of the Document",
        description="Status of the Document",
    )
    task_id: str = Field(
        ...,
        title="Task ID from celery",
        description="Task ID from celery",
    )
    metadata: dict = Field(
        ...,
        title="Metadata",
        description="Metadata",
    )

    model_config = ConfigDict(from_attributes=True)


class GetKnowledgeBase(BaseModel):
    id: UUID = Field(
        ...,
        title="Knowledge Base ID",
        description="Knowledge Base ID",
    )
    name: str = Field(
        ...,
        title="Name of the Knowledge Base",
        description="Name of the Knowledge Base",
    )
    description: str = Field(
        default="No description",
        title="Description of the Knowledge Base",
        description="Description of the Knowledge Base",
    )
    document_count: int = Field(
        ...,
        title="Number of documents in the Knowledge Base",
        description="Number of documents in the Knowledge Base",
    )
    last_updated: datetime = Field(
        ...,
        title="Last Updated time",
        description="Last Updated time",
    )


class DocumentInKnowledgeBase(BaseModel):
    id: UUID
    file_name: str
    file_type: str
    created_at: datetime
    status: str

    model_config = ConfigDict(from_attributes=True)


class GetKnowledgeBaseResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    user_id: UUID
    created_at: datetime
    updated_at: datetime
    document_count: int
    last_updated: datetime
    documents: list[DocumentInKnowledgeBase]

    model_config = ConfigDict(from_attributes=True)
