import sys
from uuid import UUID
from pathlib import Path
from fastapi import Depends
from sqlmodel import select
from llama_index.core import Document

sys.path.append(str(Path(__file__).parent.parent.parent))

from .contextual_rag_manager import ContextualRAG
from .core import MinioClient, get_session, DocumentChunks

from src.utils import get_formatted_logger
from src.constants import DocumentMetadata
from src.settings import GlobalSettings, get_default_setting

logger = get_formatted_logger(__file__)


class DatabaseManager:
    """
    Database manager to handle all the database operations
    """

    def __init__(self, setting: GlobalSettings):
        """
        Initialize the database manager

        Args:
            setting (GlobalSettings): Global settings
            sql_db_session (Session): SQL Database session
        """
        self.setting = setting

        self.minio_client = MinioClient.from_setting(setting)
        self.contextual_rag_client = ContextualRAG.from_setting(setting)

        logger.info("DatabaseManager initialized successfully !!!")

    def upload_file(self, object_name: str, file_path: str):
        """
        Upload file to Minio

        Args:
            object_name (str): Object name in Minio
            file_path (str): Local file path
        """

        self.minio_client.upload_file(
            bucket_name=self.setting.upload_bucket_name,
            object_name=object_name,
            file_path=file_path,
        )

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

    def es_index_document(
        self,
        index_name: str,
        document_id: str | UUID,
        documents_metadata: list[DocumentMetadata],
    ):
        """
        Index document in ElasticSearch

        Args:
            index_name (str): Index name
            document_id (str | UUID): Document ID
            documents_metadata (list[DocumentMetadata]): List of documents metadata
        """

        self.contextual_rag_client.es_index_document(
            index_name=index_name,
            document_id=document_id,
            documents_metadata=documents_metadata,
        )

    def es_delete_document(self, index_name: str, document_id: str | UUID):
        """
        Delete document from ElasticSearch

        Args:
            index_name (str): Index name
            document_id (str | UUID): Document ID
        """

        self.contextual_rag_client.es_delete_document(
            index_name=index_name,
            document_id=document_id,
        )

    def index_to_vector_db(
        self, collection_name: str, chunks_documents: list[Document], document_id: UUID
    ):
        """
        Index to vector database

        Args:
            collection_name (str): Collection name
            documents (list[Document]): List of documents
            document_id (UUID): Document ID
        """
        self.contextual_rag_client.insert_data(
            collection_name=collection_name,
            chunks=chunks_documents,
            document_id=document_id,
        )

    def delete_file(
        self,
        object_name: str,
        document_id: UUID,
        knownledge_base_id: UUID,
        is_contextual_rag: bool,
    ):
        """
        Delete file from Minio

        Args:
            object_name (str): Object name in Minio
            document_id (UUID): Document ID
            is_contextual_rag (bool): Is contextual RAG
        """

        self.minio_client.remove_file(
            bucket_name=self.setting.upload_bucket_name,
            object_name=object_name,
        )

        logger.debug("Removing from SQL Database ...")
        with get_session(setting=get_default_setting()) as session:
            query_document_chunks = select(DocumentChunks).where(
                DocumentChunks.document_id == document_id
            )
            document_chunks = session.exec(query_document_chunks).all()

            # Delete the document chunks before deleting the document
            for document_chunk in document_chunks:
                session.delete(document_chunk)

            session.commit()

            self.contextual_rag_client.qdrant_client.delete_vector(
                collection_name=knownledge_base_id,
                document_id=document_id,
            )

            if is_contextual_rag:
                self.es_delete_document(
                    index_name=knownledge_base_id,
                    document_id=document_id,
                )

        logger.info(f"Removed: {document_id}")


def get_db_manager(
    setting: GlobalSettings = Depends(get_default_setting),
) -> DatabaseManager:
    return DatabaseManager(setting)
