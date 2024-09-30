from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
from typing import List

class DocumentInKnowledgeBase(BaseModel):
    id: int
    file_name: str
    file_type: str
    file_path: str
    created_at: datetime
    status: str

    model_config = ConfigDict(from_attributes=True)

class KnowledgeBaseCreate(BaseModel):
    name: str
    description: Optional[str] = None

class KnowledgeBaseUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class KnowledgeBaseResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    user_id: int
    created_at: datetime
    updated_at: datetime
    document_count: int
    last_updated: datetime
    documents: List[DocumentInKnowledgeBase]

    model_config = ConfigDict(from_attributes=True)
