import os
import sys
import uuid as uuid_pkg
from pathlib import Path
from fastapi import Depends
from sqlalchemy import Column
from dotenv import load_dotenv
from datetime import datetime, UTC
from typing import List, Dict, Optional
from pydantic import EmailStr, ConfigDict
from sqlalchemy.dialects.postgresql import TEXT, JSON
from sqlmodel import SQLModel, Field, String, create_engine, Session, Relationship


sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from src.constants import FileStatus, SenderType
from src.settings import get_default_setting, GlobalSettings

load_dotenv()


def get_session(setting: GlobalSettings = Depends(get_default_setting)):
    sql_url = setting.sql_config.url

    if not sql_url:
        sql_url = os.getenv("SQL_DB_URL")

    assert sql_url, "SQL_DB_URL is not set"

    engine = create_engine(sql_url)
    SQLModel.metadata.create_all(engine)
    return Session(engine, expire_on_commit=False)


class Users(SQLModel, table=True):
    __tablename__ = "users"

    id: uuid_pkg.UUID = Field(
        default_factory=uuid_pkg.uuid4,
        primary_key=True,
        index=True,
        nullable=False,
    )
    username: str = Field(nullable=False, unique=True, description="Unique Username")
    email: EmailStr = Field(
        sa_type=String(), nullable=False, unique=True, description="Email Address"
    )
    hashed_password: str = Field(nullable=False, description="Hashed Password")

    created_at: datetime = Field(
        default_factory=datetime.now,
        nullable=False,
        description="Created At time",
    )

    updated_at: datetime = Field(
        default_factory=datetime.now,
        nullable=False,
        description="Updated At time",
        sa_column_kwargs={"onupdate": datetime.now(UTC)},
    )

    assistants: List["Assistants"] = Relationship(back_populates="user")
    conversations: List["Conversations"] = Relationship(back_populates="user")
    knowledge_bases: List["KnowledgeBases"] = Relationship(back_populates="user")

    model_config = ConfigDict(from_attributes=True)


class Assistants(SQLModel, table=True):
    __tablename__ = "assistants"

    id: uuid_pkg.UUID = Field(
        default_factory=uuid_pkg.uuid4,
        primary_key=True,
        index=True,
        nullable=False,
    )

    user_id: uuid_pkg.UUID = Field(foreign_key="users.id")
    name: str = Field(
        sa_column=Column(TEXT),
        description="Assistant Name",
    )
    description: str = Field(
        sa_column=Column(TEXT),
        description="Assistant Description",
    )
    system_prompt: str = Field(
        sa_column=Column(TEXT),
        default="You are a helpful assistant",
        description="System Prompt",
    )
    knowledge_base_id: uuid_pkg.UUID = Field(foreign_key="knowledge_bases.id")
    configuration: Optional[Dict] = Field(
        default_factory=dict,
        sa_column=Column(JSON),
        description="Configuration of the Knowledge Base",
    )
    created_at: datetime = Field(
        default_factory=datetime.now,
        nullable=False,
        description="Created At time",
    )
    updated_at: datetime = Field(
        default_factory=datetime.now,
        nullable=False,
        description="Updated At time",
        sa_column_kwargs={"onupdate": datetime.now(UTC)},
    )

    user: Users = Relationship(back_populates="assistants")
    knowledge_base: "KnowledgeBases" = Relationship(back_populates="assistant")
    conversations: List["Conversations"] = Relationship(back_populates="assistant")


class KnowledgeBases(SQLModel, table=True):
    __tablename__ = "knowledge_bases"
    id: uuid_pkg.UUID = Field(
        default_factory=uuid_pkg.uuid4,
        primary_key=True,
        index=True,
        nullable=False,
    )
    user_id: uuid_pkg.UUID = Field(foreign_key="users.id")
    name: str = Field(
        nullable=False,
        description="Name of the Knowledge Base",
    )
    description: str = Field(
        nullable=False,
        description="Description of the Knowledge Base",
    )
    is_contextual_rag: bool = Field(
        default=False,
        description="Use Contextual RAG for the Knowledge Base or not",
    )
    created_at: datetime = Field(
        default_factory=datetime.now,
        nullable=False,
        description="Created At time",
    )
    updated_at: datetime = Field(
        default_factory=datetime.now,
        nullable=False,
        description="Updated At time",
        sa_column_kwargs={"onupdate": datetime.now(UTC)},
    )

    documents: List["Documents"] = Relationship(back_populates="knowledge_base")
    assistant: "Assistants" = Relationship(back_populates="knowledge_base")
    user: "Users" = Relationship(back_populates="knowledge_bases")

    @property
    def last_updated(self):
        return self.updated_at

    @property
    def document_count(self):
        return len(self.documents)


class Documents(SQLModel, table=True):
    __tablename__ = "documents"
    id: uuid_pkg.UUID = Field(
        default_factory=uuid_pkg.uuid4,
        primary_key=True,
        index=True,
        nullable=False,
    )
    knowledge_base_id: uuid_pkg.UUID = Field(foreign_key="knowledge_bases.id")
    file_name: str = Field(
        nullable=False,
        description="File Name of the Document",
    )
    file_path_in_minio: str = Field(
        nullable=False,
        description="Path of the Document",
    )
    file_type: str = Field(
        nullable=False,
        description="File extension",
    )
    status: FileStatus = Field(
        nullable=False,
        description="Status of the Document",
    )
    created_at: datetime = Field(
        default_factory=datetime.now,
        nullable=False,
        description="Created At time",
    )
    updated_at: datetime = Field(
        default_factory=datetime.now,
        nullable=False,
        description="Updated At time",
        sa_column_kwargs={"onupdate": datetime.now(UTC)},
    )
    task_id: str = Field(
        nullable=True,
        description="Task ID from celery task queue",
    )

    @property
    def file_path(self):
        return self.file_path_in_minio

    knowledge_base: KnowledgeBases = Relationship(back_populates="documents")
    document_chunks: List["DocumentChunks"] = Relationship(back_populates="document")


class DocumentChunks(SQLModel, table=True):
    __tablename__ = "document_chunks"
    id: uuid_pkg.UUID = Field(
        default_factory=uuid_pkg.uuid4,
        primary_key=True,
        index=True,
        nullable=False,
    )
    document_id: uuid_pkg.UUID = Field(foreign_key="documents.id")
    chunk_index: int = Field(
        nullable=False,
        description="Index of the Chunk in the origin document",
    )
    content: str = Field(
        sa_column=Column(TEXT),
        description="Content of the Chunk",
    )
    vector_id: str = Field(
        nullable=True,
        description="Vector ID of the Chunk from vector database",
    )
    created_at: datetime = Field(
        default_factory=datetime.now,
        nullable=False,
        description="Created At time",
    )
    updated_at: datetime = Field(
        default_factory=datetime.now,
        nullable=False,
        description="Updated At time",
        sa_column_kwargs={"onupdate": datetime.now(UTC)},
    )

    document: Documents = Relationship(back_populates="document_chunks")


class Conversations(SQLModel, table=True):
    __tablename__ = "conversations"
    id: uuid_pkg.UUID = Field(
        default_factory=uuid_pkg.uuid4,
        primary_key=True,
        index=True,
        nullable=False,
    )
    user_id: uuid_pkg.UUID = Field(foreign_key="users.id")
    assistant_id: uuid_pkg.UUID = Field(foreign_key="assistants.id")
    started_at: datetime = Field(
        default_factory=datetime.now,
        nullable=False,
        description="Conversation Start Time",
    )
    ended_at: datetime = Field(
        nullable=True,
        description="Conversation End Time",
    )

    created_at: datetime = Field(
        default_factory=datetime.now,
        nullable=False,
        description="Created At time",
    )
    updated_at: datetime = Field(
        default_factory=datetime.now,
        nullable=False,
        description="Updated At time",
        sa_column_kwargs={"onupdate": datetime.now(UTC)},
    )

    user: Users = Relationship(back_populates="conversations")
    assistant: Assistants = Relationship(back_populates="conversations")
    messages: List["Messages"] = Relationship(back_populates="conversation")


class Messages(SQLModel, table=True):
    __tablename__ = "messages"
    id: uuid_pkg.UUID = Field(
        default_factory=uuid_pkg.uuid4,
        primary_key=True,
        index=True,
        nullable=False,
    )
    conversation_id: uuid_pkg.UUID = Field(foreign_key="conversations.id")
    sender_type: SenderType = Field(
        nullable=False,
        description="Sender Type",
    )
    content: str = Field(
        sa_column=Column(TEXT),
        description="Content of the Message",
    )
    created_at: datetime = Field(
        default_factory=datetime.now,
        nullable=False,
        description="Created At time",
    )
    updated_at: datetime = Field(
        default_factory=datetime.now,
        nullable=False,
        description="Updated At time",
        sa_column_kwargs={"onupdate": datetime.now(UTC)},
    )

    conversation: Conversations = Relationship(back_populates="messages")


def init_db():
    sql_url = os.getenv("SQL_DB_URL")
    assert sql_url, "SQL_DB_URL is not set"

    engine = create_engine(sql_url)
    SQLModel.metadata.create_all(engine)


init_db()
