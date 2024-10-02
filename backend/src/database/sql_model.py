import os
import sys
from typing import List
import uuid as uuid_pkg
from pathlib import Path
from sqlalchemy import Column
from dotenv import load_dotenv
from datetime import datetime, UTC
from pydantic import EmailStr, ConfigDict
from sqlalchemy.dialects.postgresql import TEXT
from sqlmodel import SQLModel, Field, String, create_engine, Session, Relationship


sys.path.append(str(Path(__file__).parent.parent.parent))

from src.constants import DocumentStatus, SenderType

load_dotenv()


def init_db(sql_url: str = None):

    if not sql_url:
        sql_url = os.getenv("SQL_DB_URL")

    assert sql_url, "SQL_DB_URL is not set"

    engine = create_engine(sql_url)
    SQLModel.metadata.create_all(engine)
    return engine


def get_session():
    engine = create_engine(os.getenv("SQL_DB_URL"))
    with Session(engine) as session:
        yield session


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
    file_path: str = Field(
        nullable=False,
        description="Path of the Document",
    )
    file_type: str = Field(
        nullable=False,
        description="File extension",
    )
    status: DocumentStatus = Field(
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
