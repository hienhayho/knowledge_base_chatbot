import sys
from uuid import UUID
from pathlib import Path
from datetime import datetime
from pydantic import BaseModel, Field

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
