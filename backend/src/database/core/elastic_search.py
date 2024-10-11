import sys
from uuid import UUID
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from elasticsearch.helpers import bulk
from elasticsearch import Elasticsearch
from llama_index.core.bridge.pydantic import Field

from src.utils import get_formatted_logger
from src.constants import DocumentMetadata, ElasticSearchResponse

logger = get_formatted_logger(__file__)


class ElasticSearch:
    """
    ElasticSearch client to index and search documents for contextual RAG.
    """

    url: str = Field(..., description="Elastic Search URL")

    def __init__(self, url: str):
        """
        Initialize the ElasticSearch client.

        Args:
            url (str): URL of the ElasticSearch server
        """

        self.es_client = Elasticsearch(url)
        self.test_connection()
        logger.info("ElasticSearch client initialized successfully !!!")

    def test_connection(self):
        """
        Test the connection with the ElasticSearch server.
        """
        if not self.es_client.ping():
            logger.error("ElasticSearch connection failed")
            raise ConnectionError("ElasticSearch connection failed")

    def create_index(self, index_name: str):
        """
        Create the index for contextual RAG from provided index name.

        Args:
            index_name (str): UUID of the **knowledge_base_id** to be created
        """
        index_settings = {
            "settings": {
                "analysis": {"analyzer": {"default": {"type": "english"}}},
                "similarity": {"default": {"type": "BM25"}},
                "index.queries.cache.enabled": False,  # Disable query cache
            },
            "mappings": {
                "properties": {
                    "content": {"type": "text", "analyzer": "english"},
                    "contextualized_content": {"type": "text", "analyzer": "english"},
                    "vector_id": {"type": "text", "index": True},
                    "document_id": {"type": "text", "index": True},
                }
            },
        }

        self.es_client.indices.create(index=index_name, body=index_settings)
        logger.info(f"Index: {index_name} created successfully !!!")

    def check_index_exists(self, index_name: str) -> bool:
        """
        Check if the index exists in the ElasticSearch.

        Args:
            index_name (str): Name of the index to check

        Returns:
            bool: True if index exists, False otherwise
        """
        return self.es_client.indices.exists(index=index_name)

    def index_documents(
        self,
        index_name: str,
        document_id: str | UUID,
        documents_metadata: list[DocumentMetadata],
    ) -> bool:
        """
        Index the documents to the ElasticSearch index.

        Args:
            index_name (str): Name of the index to index documents
            document_id (str | UUID): Document ID to index
            documents_metadata (list[DocumentMetadata]): List of documents metadata to index.
        """
        document_id = str(document_id)
        logger.debug(
            "index_name: %s - len(documents_metadata): %s",
            index_name,
            len(documents_metadata),
        )

        if not self.check_index_exists(index_name):
            logger.debug(
                f"Index: {index_name} does not exist. Automatically creating index..."
            )
            self.create_index(index_name)

        actions = [
            {
                "_index": index_name,
                "_source": {
                    "vector_id": metadata.vector_id,
                    "content": metadata.original_content,
                    "contextualized_content": metadata.contextualized_content,
                    "document_id": document_id,
                },
            }
            for metadata in documents_metadata
        ]

        success, _ = bulk(self.es_client, actions)

        self.es_client.indices.refresh(index=index_name)

        return success

    def search(
        self, index_name: str, query: str, top_k: int = 20
    ) -> list[ElasticSearchResponse]:
        """
        Search the documents relevant to the query.

        Args:
            index_name (str): Name of the index to search
            query (str): Query to search
            top_k (int): Number of documents to return

        Returns:
            list[ElasticSearchResponse]: List of ElasticSearch response objects.
        """
        logger.info("index_name: %s - query: %s - top_k: %s", index_name, query, top_k)

        self.es_client.indices.refresh(
            index=index_name
        )  # Force refresh before each search
        search_body = {
            "query": {
                "multi_match": {
                    "query": query,
                    "fields": ["content", "contextualized_content"],
                }
            },
            "size": top_k,
        }
        response = self.es_client.search(index=index_name, body=search_body)

        return [
            ElasticSearchResponse(
                vector_id=hit["_source"]["vector_id"],
                content=hit["_source"]["content"],
                contextualized_content=hit["_source"]["contextualized_content"],
                score=hit["_score"],
            )
            for hit in response["hits"]["hits"]
        ]

    def delete_documents(self, index_name: str | UUID, document_id: str | UUID):
        """
        Delete the documents from the index.

        Args:
            index_name (str | UUID): Name of the index to delete documents
            document_id (str | UUID): Document ID to delete
        """
        document_id = str(document_id)
        index_name = str(index_name)

        if not self.check_index_exists(index_name):
            logger.debug(f"Index: {index_name} does not exist")
            return

        logger.debug("index_name: %s - document_id: %s", index_name, document_id)

        self.es_client.delete_by_query(
            index=index_name,
            query={
                "match": {
                    "document_id": document_id,
                }
            },
        )

        self.es_client.indices.refresh(index=index_name)

    def get_all_data_in_index(self, index_name: str) -> list[ElasticSearchResponse]:
        """
        Get all the data in the index.

        Args:
            index_name (str): Name of the index to get all data

        Returns:
            list[dict]: List of all data in the index
        """
        self.es_client.indices.refresh(index=index_name)
        response = self.es_client.search(
            index=index_name, body={"query": {"match_all": {}}}
        )

        return [
            ElasticSearchResponse(
                vector_id=hit["_source"]["vector_id"],
                content=hit["_source"]["content"],
                contextualized_content=hit["_source"]["contextualized_content"],
                document_id=hit["_source"]["document_id"],
            )
            for hit in response["hits"]["hits"]
        ]

    def migrate_index(self, target_index_name: str, source_index_name: str):
        """
        Migrate the data from source index to target index.

        Args:
            target_index_name (str): Name of the target index
            source_index_name (str): Name of the source index
        """
        if not self.check_index_exists(source_index_name):
            logger.debug(f"Source index: {source_index_name} does not exist")
            return

        if not self.check_index_exists(target_index_name):
            logger.debug(f"Target index: {target_index_name} does not exist")
            self.create_index(target_index_name)

        self.es_client.reindex(
            body={
                "source": {"index": source_index_name},
                "dest": {"index": target_index_name},
            }
        )

        self.es_client.indices.refresh(index=target_index_name)
        logger.debug(
            f"Index: {source_index_name} migrated to {target_index_name} successfully !!!"
        )

        self.es_client.indices.delete(index=source_index_name)
        logger.debug("Removed source index: %s", source_index_name)
