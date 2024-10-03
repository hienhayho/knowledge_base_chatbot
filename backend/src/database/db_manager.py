import sys
from pathlib import Path
from fastapi import Depends
from llama_index.core import Document

sys.path.append(str(Path(__file__).parent.parent.parent))

from .core import MinioClient
from .contextual_rag_manager import ContextualRAG

from src.utils import get_formatted_logger
from src.constants import DocumentMetadata
from src.settings import GlobalSettings, get_default_setting

logger = get_formatted_logger(__file__, file_path="logs/database_manager.log")


class DatabaseManager:
    """
    Database manager to handle all the database operations
    """

    def __init__(self, setting: GlobalSettings):
        """
        Initialize the database manager

        Args:
            sql_url (str): SQL database URL
            minio_client (MinioClient): Minio client
            vector_db_client (BaseVectorDatabase): Vector database
            elastic_search_client (ElasticSearch): ElasticSearch client
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

    def get_chunks(self, document: Document) -> list[list[Document]]:
        """
        Get contextual RAG chunks

        Args:
            document (Document): Raw document

        Returns:
            list[list[Document]]: List of contextual RAG chunks
        """

        return self.contextual_rag_client.split_document(document)

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
        self, index_name: str, documents_metadata: list[DocumentMetadata]
    ):
        """
        Index document in ElasticSearch

        Args:
            index_name (str): Index name
            documents_metadata (list[DocumentMetadata]): List of documents metadata
        """

        self.contextual_rag_client.es_index_document(
            index_name=index_name, documents_metadata=documents_metadata
        )

    def index_to_vector_db(
        self,
        collection_name: str,
        documents: list[Document],
    ):
        """
        Index to vector database

        Args:
            collection_name (str): Collection name
            vector_id (str): Vector ID
            vector (list[float]): Vector
            payload (QdrantPayload): Payload
        """
        self.contextual_rag_client.insert_data(
            collection_name=collection_name,
            documents=documents,
        )


def get_db_manager(
    setting: GlobalSettings = Depends(get_default_setting),
) -> DatabaseManager:
    return DatabaseManager(setting)
