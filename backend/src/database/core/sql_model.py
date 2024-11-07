import os
import sys
import uuid as uuid_pkg
from pathlib import Path
from fastapi import Depends
from sqlalchemy import Column
from dotenv import load_dotenv
from datetime import datetime
from contextlib import contextmanager
from typing import List, Dict, Optional
from pydantic import EmailStr, ConfigDict
from sqlalchemy.dialects.postgresql import TEXT, JSON
from sqlmodel import SQLModel, Field, String, create_engine, Session, UUID
from sqlalchemy.dialects.postgresql import ARRAY

sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from src.constants import FileStatus, SenderType, UserRole
from src.settings import get_default_setting, GlobalSettings

load_dotenv()


def get_instance_session():
    sql_url = os.getenv("SQL_DB_URL")
    assert sql_url, "SQL_DB_URL is not set"
    engine = create_engine(
        sql_url,
        pool_pre_ping=True,
        connect_args={
            "keepalives": 1,
            "keepalives_idle": 30,
            "keepalives_interval": 10,
            "keepalives_count": 5,
        },
    )
    SQLModel.metadata.create_all(engine)
    session = Session(engine, expire_on_commit=False)
    return session


def get_session(setting: GlobalSettings = Depends(get_default_setting)):
    sql_url = setting.sql_config.url

    if not sql_url:
        sql_url = os.getenv("SQL_DB_URL")

    assert sql_url, "SQL_DB_URL is not set"

    engine = create_engine(
        sql_url,
        pool_pre_ping=True,
        connect_args={
            "keepalives": 1,
            "keepalives_idle": 30,
            "keepalives_interval": 10,
            "keepalives_count": 5,
        },
    )
    SQLModel.metadata.create_all(engine)
    session = Session(engine, expire_on_commit=False)
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@contextmanager
def get_session_manager(setting: GlobalSettings = Depends(get_default_setting)):
    sql_url = setting.sql_config.url
    if not sql_url:
        sql_url = os.getenv("SQL_DB_URL")

    assert sql_url, "SQL_DB_URL is not set"

    engine = create_engine(
        sql_url,
        pool_pre_ping=True,
        connect_args={
            "keepalives": 1,
            "keepalives_idle": 30,
            "keepalives_interval": 10,
            "keepalives_count": 5,
        },
    )
    session = Session(engine, expire_on_commit=False)
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


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

    role: UserRole = Field(
        default=UserRole.USER,
        description="Role of the User",
    )
    organization: str = Field(
        nullable=True,
        description="Organization of the User",
    )
    is_owner: bool = Field(
        default=False,
        description="Is the user owner of the organization",
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
        sa_column_kwargs={"onupdate": datetime.now()},
    )
    max_size_mb: float = Field(
        default=5.0,
        description="Max Size of files user can upload to the knowledge bases",
    )

    def total_upload_size(
        self, user_kbs: List["KnowledgeBases"], documents: List["Documents"]
    ) -> float:
        """
        Total size of the files uploaded by the user in MB

        Args:
            user_kbs (List[KnowledgeBases]): List of Knowledge Bases of the user

        Returns:
            float: Total size of the files uploaded by the user in MB
        """
        # In MB
        return sum([kb.files_size(documents=documents) for kb in user_kbs])

    def allow_upload(
        self,
        current_file_size: float,
        user_kbs: List["KnowledgeBases"],
        documents: List["Documents"],
    ) -> bool:
        """
        Check if the user can upload the file of given size

        Args:
            current_file_size (float): Size of the file in BYTES
            user_kbs (List[KnowledgeBases]): List of Knowledge Bases of the user

        Returns:
            bool: True if user can upload the file, False otherwise
        """
        return (
            self.total_upload_size(user_kbs, documents)
            + current_file_size / 1024 / 1024
            < self.max_size_mb
        )

    model_config = ConfigDict(from_attributes=True)


class Assistants(SQLModel, table=True):
    __tablename__ = "assistants"

    id: uuid_pkg.UUID = Field(
        default_factory=uuid_pkg.uuid4,
        primary_key=True,
        index=True,
        nullable=False,
    )

    user_id: uuid_pkg.UUID = Field(nullable=False)
    name: str = Field(
        sa_column=Column(TEXT),
        description="Assistant Name",
    )
    description: str = Field(
        sa_column=Column(TEXT),
        description="Assistant Description",
    )
    guard_prompt: str = Field(
        sa_column=Column(TEXT),
        default="",
        description="Guard Prompt that user not want to be included in asisistant's response",
    )
    interested_prompt: str = Field(
        sa_column=Column(TEXT),
        default="",
        description="Interested Prompt that user want to focus on",
    )
    knowledge_base_id: uuid_pkg.UUID = Field(nullable=False)
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
        sa_column_kwargs={"onupdate": datetime.now()},
    )

    def total_cost(
        self, conversations: list["Conversations"], messages: list[list["Messages"]]
    ) -> float:
        return sum(
            [
                conversation.total_cost(messages)
                for conversation, messages in zip(conversations, messages)
            ]
        )


class KnowledgeBases(SQLModel, table=True):
    __tablename__ = "knowledge_bases"
    id: uuid_pkg.UUID = Field(
        default_factory=uuid_pkg.uuid4,
        primary_key=True,
        index=True,
        nullable=False,
    )
    user_id: uuid_pkg.UUID = Field(nullable=False)
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
    parents: List[uuid_pkg.UUID] = Field(
        default=[],
        sa_column=Column(ARRAY(UUID)),
        description="List of KBs from which this KB is derived",
    )
    children: List[uuid_pkg.UUID] = Field(
        default=[],
        sa_column=Column(ARRAY(UUID)),
        description="List of KBs which are derived from this KB",
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
        sa_column_kwargs={"onupdate": datetime.now()},
    )

    # @property
    def files_size(self, documents: List["Documents"]) -> float:
        return sum([document.file_size for document in documents]) / 1024 / 1024

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
    knowledge_base_id: uuid_pkg.UUID = Field(nullable=False)
    user_id: uuid_pkg.UUID = Field(nullable=False)
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
        sa_column_kwargs={"onupdate": datetime.now()},
    )
    task_id: str = Field(
        nullable=True,
        description="Task ID from celery task queue",
    )
    file_size: float = Field(
        nullable=False,
        description="Size of the file in bytes",
    )

    @property
    def file_size_in_mb(self):
        return self.file_size / 1024 / 1024

    @property
    def file_path(self):
        return self.file_path_in_minio


class DocumentChunks(SQLModel, table=True):
    __tablename__ = "document_chunks"
    id: uuid_pkg.UUID = Field(
        default_factory=uuid_pkg.uuid4,
        primary_key=True,
        index=True,
        nullable=False,
    )
    document_id: uuid_pkg.UUID = Field(nullable=False)
    chunk_index: int = Field(
        nullable=False,
        description="Index of the Chunk in the origin document",
    )
    original_content: str = Field(
        sa_column=Column(TEXT),
        description="Original Content of the Chunk",
    )
    content: str = Field(
        sa_column=Column(TEXT),
        description="Content of the Chunk after adding context",
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
        sa_column_kwargs={"onupdate": datetime.now()},
    )


class Conversations(SQLModel, table=True):
    __tablename__ = "conversations"
    id: uuid_pkg.UUID = Field(
        default_factory=uuid_pkg.uuid4,
        primary_key=True,
        index=True,
        nullable=False,
    )

    name: str = Field(
        default="",
        description="Name of the Conversation (Optional)",
    )

    user_id: uuid_pkg.UUID = Field(nullable=False)

    assistant_id: uuid_pkg.UUID = Field(nullable=False)

    started_at: datetime = Field(
        default_factory=datetime.now,
        nullable=False,
        description="Conversation Start Time",
    )

    ended_at: datetime = Field(
        nullable=True,
        description="Conversation End Time",
    )

    number_of_sessions: int = Field(
        default=0,
        description="Number of Sessions in the Conversation",
    )

    session_chat_time: float = Field(
        default=0.0,
        description="Chat Time of the Conversation in seconds.",
    )

    user_messages: int = Field(
        default=0,
        description="Number of user's messages in all sessions chat.",
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
        sa_column_kwargs={"onupdate": datetime.now()},
    )

    def total_cost(self, messages: list["Messages"]) -> float:
        return sum([message.cost for message in messages])

    @property
    def average_session_chat_time(self) -> float:
        return (
            0
            if self.number_of_sessions == 0
            else round(self.session_chat_time / self.number_of_sessions, 2)
        )

    @property
    def average_user_messages(self) -> float:
        return (
            0
            if self.number_of_sessions == 0
            else int(self.user_messages / self.number_of_sessions)
        )


class Messages(SQLModel, table=True):
    __tablename__ = "messages"
    id: uuid_pkg.UUID = Field(
        default_factory=uuid_pkg.uuid4,
        primary_key=True,
        index=True,
        nullable=False,
    )
    conversation_id: uuid_pkg.UUID = Field(nullable=False)
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
        sa_column_kwargs={"onupdate": datetime.now()},
    )

    cost: float = Field(
        default=0.0,
        description="Cost of the message, if from user then 0.0, else any other positive value",
    )
    is_chat_false: bool = Field(
        nullable=True,
        description="If the assistant response message is correct with the query and context. If the message is from user then it is None",
    )

    response_time: float = Field(
        nullable=True,
        description="Response time of the assistant in seconds",
    )


def init_db():
    sql_url = os.getenv("SQL_DB_URL")
    assert sql_url, "SQL_DB_URL is not set"

    engine = create_engine(
        sql_url,
        pool_pre_ping=True,
        connect_args={
            "keepalives": 1,
            "keepalives_idle": 30,
            "keepalives_interval": 10,
            "keepalives_count": 5,
        },
    )
    SQLModel.metadata.create_all(engine)


init_db()
