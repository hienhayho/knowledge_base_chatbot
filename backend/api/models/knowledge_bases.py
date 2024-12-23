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


class InheritKnowledgeBaseRequest(BaseModel):
    source_knowledge_base_id: UUID = Field(
        ...,
        title="Source Knowledge Base ID",
        description="Source Knowledge Base ID",
    )
    target_knowledge_base_id: UUID | None = Field(
        None,
        title="Target Knowledge Base ID",
        description="Target Knowledge Base ID",
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
    created_at: datetime = Field(
        ...,
        title="Created At time",
        description="Created At time",
    )
    knowledge_base: KnowledgeBases = Field(
        ...,
        title="Knowledge Base",
        description="Knowledge Base",
    )
    file_size_in_mb: float = Field(
        ...,
        title="File Size in MB",
        description="File Size in MB",
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


class DeleteDocumentRequestBody(BaseModel):
    delete_to_retry: bool = Field(
        default=False,
        title="Delete file content in previous attempt",
        description="Delete file content in previous attempt",
    )


class DocumentInKnowledgeBase(BaseModel):
    id: UUID
    file_name: str
    file_type: str
    created_at: datetime
    status: str
    file_size_in_mb: float

    model_config = ConfigDict(from_attributes=True)


class InheritableKnowledgeBaseResponse(BaseModel):
    id: UUID
    name: str


class GetKnowledgeBaseResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    user_id: UUID
    created_at: datetime
    updated_at: datetime
    document_count: int
    last_updated: datetime
    parents: list[UUID]
    children: list[UUID]
    documents: list[DocumentInKnowledgeBase]
    inheritable_knowledge_bases: list[InheritableKnowledgeBaseResponse]

    model_config = ConfigDict(from_attributes=True)
