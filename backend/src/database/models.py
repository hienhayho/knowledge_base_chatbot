from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, JSON, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

Base = declarative_base()


class DocumentStatus(enum.Enum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"


# SQLAlchemy models
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    knowledge_bases = relationship("KnowledgeBase", back_populates="user")
    assistants = relationship("Assistant", back_populates="user")


class KnowledgeBase(Base):
    __tablename__ = "knowledge_bases"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String(100), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user = relationship("User", back_populates="knowledge_bases")
    documents = relationship("Document", back_populates="knowledge_base")

    @property
    def document_count(self):
        return len(self.documents)

    @property
    def last_updated(self):
        if not self.documents:
            return self.updated_at
        return max(doc.created_at for doc in self.documents + [self])


class Document(Base):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True)
    knowledge_base_id = Column(Integer, ForeignKey("knowledge_bases.id"))
    file_name = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False)
    file_path = Column(String(255), nullable=False)
    status = Column(Enum(DocumentStatus), default=DocumentStatus.UPLOADED)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    knowledge_base = relationship("KnowledgeBase", back_populates="documents")
    chunks = relationship("DocumentChunk", back_populates="document")
    task_id = Column(String(255))


class DocumentChunk(Base):
    __tablename__ = "document_chunks"
    id = Column(Integer, primary_key=True)
    document_id = Column(Integer, ForeignKey("documents.id"))
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    vector_id = Column(String(36), nullable=False)  # UUID as string
    created_at = Column(DateTime, default=datetime.utcnow)
    document = relationship("Document", back_populates="chunks")


class Assistant(Base):
    __tablename__ = "assistants"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String(100), nullable=False)
    description = Column(Text)
    systemprompt = Column(Text)
    knowledge_base_id = Column(Integer, ForeignKey("knowledge_bases.id"))
    configuration = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user = relationship("User", back_populates="assistants")
    knowledge_base = relationship("KnowledgeBase")


class Conversation(Base):
    __tablename__ = "conversations"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    assistant_id = Column(Integer, ForeignKey("assistants.id"))
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime)
    user = relationship("User")
    assistant = relationship("Assistant")
    messages = relationship("Message", back_populates="conversation")


class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"))
    sender_type = Column(String(10), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    conversation = relationship("Conversation", back_populates="messages")
