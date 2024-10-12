import sys
import threading
from uuid import UUID
from pathlib import Path
from fastapi import Depends
from llama_index.core import Document

sys.path.append(str(Path(__file__).parent.parent.parent))

from .contextual_rag_manager import ContextualRAG
from .core import MinioClient

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
        """
        self.setting = setting

        self.minio_client = MinioClient.from_setting(setting)
        self.contextual_rag_client = ContextualRAG.from_setting(setting)

        logger.info("DatabaseManager initialized successfully !!!")

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
        self.contextual_rag_client.qdrant_insert_data(
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

        self.contextual_rag_client.qdrant_client.delete_vector(
            collection_name=knownledge_base_id,
            document_id=document_id,
        )

        if is_contextual_rag:
            self.contextual_rag_client.es_delete_document(
                index_name=knownledge_base_id,
                document_id=document_id,
            )

        logger.info(f"Removed: {document_id}")

    def es_migrate(
        self, target_knowledge_base_id: str, source_knowledge_base_ids: list[str]
    ):
        """
        Migrate ElasticSearch index

        Args:
            target_knowledge_base_id (str): Target knowledge base ID
            source_knowledge_base_id (str): Source knowledge base ID
        """
        logger.debug(
            "Merging source knowledge bases: %s into target knowledge base: %s",
            source_knowledge_base_ids,
            target_knowledge_base_id,
        )
        for source_knowledge_base_id in source_knowledge_base_ids:
            self.contextual_rag_client.es.migrate_index(
                target_index_name=target_knowledge_base_id,
                source_index_name=source_knowledge_base_id,
            )

    def vector_db_migrate(
        self, target_knowledge_base_id: str, source_knowledge_base_ids: list[str]
    ):
        """
        Migrate Qdrant index

        Args:
            target_knowledge_base_id (str): Target knowledge base ID
            source_knowledge_base_id (str): Source knowledge base ID
        """
        logger.debug(
            "Merging source knowledge bases: %s into target knowledge base: %s",
            source_knowledge_base_ids,
            target_knowledge_base_id,
        )
        for source_knowledge_base_id in source_knowledge_base_ids:
            self.contextual_rag_client.qdrant_client.migrate_collection(
                source_collection=source_knowledge_base_id,
                target_collection=target_knowledge_base_id,
            )

    def merge_knowledge_bases(
        self,
        target_knowledge_base_id: str,
        source_knowledge_base_ids: list[str],
    ):
        """
        Merge knowledge bases

        Args:
            target_knowledge_base_id (str): Target knowledge base ID
            source_knowledge_base_ids (list[str]): Source knowledge base IDs to be merged into target knowledge base
        """
        ts = [
            threading.Thread(
                target=self.es_migrate,
                args=(target_knowledge_base_id, source_knowledge_base_ids),
            ),
            threading.Thread(
                target=self.vector_db_migrate,
                args=(target_knowledge_base_id, source_knowledge_base_ids),
            ),
        ]

        for t in ts:
            t.start()

        for t in ts:
            t.join()

        logger.debug("Merged knowledge bases successfully !!!")


def get_db_manager(
    setting: GlobalSettings = Depends(get_default_setting),
) -> DatabaseManager:
    return DatabaseManager(setting)
