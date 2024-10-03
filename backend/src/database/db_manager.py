import sys
from pathlib import Path
from llama_index.core import Document

sys.path.append(str(Path(__file__).parent.parent.parent))

from .core import MinioClient
from .contextual_rag_manager import ContextualRAG

from src.settings import GlobalSettings
from src.utils import get_formatted_logger

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

    def get_contextual_rag_chunks(self, document: Document) -> list[Document]:
        """
        Get contextual RAG chunks

        Args:
            document (Document): Raw document

        Returns:
            list[Document]: List of contextual RAG chunks
        """

        return self.contextual_rag_client.split_document(document)
