import sys
from uuid import UUID
from pathlib import Path
from typing import Optional
from fastapi import Depends, HTTPException, status
from sqlmodel import Session, select
from llama_index.core import Document

sys.path.append(str(Path(__file__).parent.parent.parent))

from .contextual_rag_manager import ContextualRAG
from .core import (
    MinioClient,
    get_instance_session,
    Messages,
    Conversations,
    Assistants,
    Documents,
)

from src.utils import get_formatted_logger
from src.constants import DocumentMetadata, DOWNLOAD_FOLDER
from src.settings import GlobalSettings, get_default_setting

logger = get_formatted_logger(__file__)


class DatabaseManager:
    """
    Database manager to handle all the database operations
    """

    def __init__(self, setting: GlobalSettings, db_session: Optional[Session] = None):
        """
        Initialize the database manager

        Args:
            setting (GlobalSettings): Global settings
        """
        self.setting = setting
        if db_session is None:
            self.db_session = get_instance_session()
        else:
            self.db_session = db_session

        self.minio_client = MinioClient.from_setting(setting)
        self.contextual_rag_client = ContextualRAG.from_setting(setting)

        logger.info("DatabaseManager initialized successfully !!!")

    @classmethod
    def from_setting(cls, setting: GlobalSettings, db_session: Session = None):
        """
        Initialize the database manager from setting

        Args:
            setting (GlobalSettings): Global settings

        Returns:
            DatabaseManager: Database manager instance
        """
        return cls(setting, db_session)

    def upload_file(self, object_name: str, file_path: str | Path):
        """
        Upload file to Minio

        Args:
            object_name (str): Object name in Minio
            file_path (str | Path): Local file path
        """

        self.minio_client.upload_file(
            bucket_name=self.setting.upload_bucket_name,
            object_name=object_name,
            file_path=file_path,
        )

    def get_product_file_path(self, knowledge_base_id: str) -> str:
        """
        Get product file path

        Args:
            knowledge_base_id (str): Knowledge base ID

        Returns:
            str: Product file path or None
        """
        with self.db_session as session:
            query = select(Documents.file_path_in_minio).where(
                Documents.knowledge_base_id == knowledge_base_id,
                Documents.is_product_file,
            )
            product_file_path = session.exec(query).first()
            file_path_to_save = str(DOWNLOAD_FOLDER / f"{knowledge_base_id}.xlsx")

            if product_file_path:
                self.download_file(product_file_path, file_path_to_save)
                return file_path_to_save

            return None

    def download_file(self, object_name: str, file_path: str):
        """
        Download file from Minio

        Args:
            object_name (str): Object name in Minio
            file_path (str): Local file path
        """

        self.minio_client.download_file(
            bucket_name=self.setting.upload_bucket_name,
            object_name=object_name,
            file_path=file_path,
        )

    def get_chunks(
        self, document: list[Document], document_id: UUID
    ) -> list[list[Document]]:
        """
        Get contextual RAG chunks

        Args:
            document (Document): Raw document
            document_id (UUID): Document ID

        Returns:
            list[list[Document]]: List of contextual RAG chunks
        """

        return self.contextual_rag_client.split_document(document, document_id)

    def get_contextual_rag_chunks(
        self, documents: list[Document], chunks: list[list[Document]]
    ) -> tuple[list[Document], list[DocumentMetadata]]:
        """
        Add contextual RAG chunk

        Args:
            documents (Document): Documents to add
            chunks (list[Document]): List of chunks from the document

        Returns:
            tuple[list[Document], list[DocumentMetadata]]: List of contextual documents and its metadata
        """

        contextual_documents, contextual_documents_metadata = (
            self.contextual_rag_client.get_contextual_documents(
                raw_documents=documents,
                splited_documents=chunks,
            )
        )

        return contextual_documents, contextual_documents_metadata

    def index_to_vector_db(
        self, kb_id: str, chunks_documents: list[Document], document_id: UUID
    ):
        """
        Index to vector database

        Args:
            kb_id (str): Knowledge base ID
            documents (list[Document]): List of documents
            document_id (UUID): Document ID
        """
        self.contextual_rag_client.qdrant_insert_data(
            kb_id=kb_id,
            chunks=chunks_documents,
            document_id=document_id,
        )

    def delete_file(
        self,
        object_name: str,
        document_id: UUID,
        delete_to_retry: bool = False,
    ):
        """
        Delete file

        Args:
            object_name (str): Object name in Minio
            document_id (UUID): Document ID
            knownledge_base_id (UUID): Knowledge base ID
            is_contextual_rag (bool): Is contextual RAG
            delete_to_retry (bool, optional): Delete file to retry processing. Defaults to `False`.
        """

        if not delete_to_retry:
            self.minio_client.remove_file(
                bucket_name=self.setting.upload_bucket_name,
                object_name=object_name,
            )

        self.contextual_rag_client.qdrant_client.delete_vector(
            collection_name=self.setting.global_vector_db_collection_name,
            document_id=document_id,
        )

        logger.info(f"Removed: {document_id}")

    def delete_conversation(self, conversation_id: str | UUID):
        """
        Delete conversation

        Args:
            conversation_id (str | UUID): Conversation ID
            assistant_id (str | UUID): Assistant ID
        """
        with self.db_session as session:
            conversation = session.exec(
                select(Conversations).where(
                    Conversations.id == conversation_id,
                )
            ).first()

            if not conversation:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Conversation not found",
                )

            messages = session.exec(
                select(Messages).where(Messages.conversation_id == conversation_id)
            ).all()

            for message in messages:
                session.delete(message)
                session.commit()

            session.delete(conversation)
            session.commit()

            session.close()

        logger.info("Deleting memory from crewAI, conversation_id: %s", conversation_id)
        # Delete collection which are memory from crewAI
        self.contextual_rag_client.qdrant_client.delete_collection(
            collection_name=f"entity_memory_{conversation_id}"
        )
        self.contextual_rag_client.qdrant_client.delete_collection(
            collection_name=f"short_term_memory_{conversation_id}"
        )

        logger.info(f"Deleted conversation: {conversation_id}")

    def delete_assistant(self, assistant_id: str | UUID):
        """
        Delete assistant

        Args:
            assistant_id (str | UUID): Assistant ID
        """
        with self.db_session as session:
            assistant = session.exec(
                select(Assistants).where(Assistants.id == assistant_id)
            ).first()

            if not assistant:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Assistant not found",
                )

            conversations_ids = session.exec(
                select(Conversations.id).where(
                    Conversations.assistant_id == assistant_id
                )
            ).all()

            for conversation_id in conversations_ids:
                self.delete_conversation(conversation_id)

            session.delete(assistant)
            session.commit()

            session.close()
        logger.info(f"Deleted assistant: {assistant_id}")


def get_db_manager(
    setting: GlobalSettings = Depends(get_default_setting),
) -> DatabaseManager:
    return DatabaseManager(setting)
