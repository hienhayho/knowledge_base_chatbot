import sys
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
        logger.info("ElasticSearch client initialized successfully !!!")

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
                    "doc_id": {"type": "text", "index": False},
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
        self, index_name: str, documents_metadata: list[DocumentMetadata]
    ) -> bool:
        """
        Index the documents to the ElasticSearch index.

        Args:
            index_name (str): Name of the index to index documents
            documents_metadata (list[DocumentMetadata]): List of documents metadata to index.
        """
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
                    "doc_id": metadata.doc_id,
                    "content": metadata.original_content,
                    "contextualized_content": metadata.contextualized_content,
                },
            }
            for metadata in documents_metadata
        ]

        success, _ = bulk(self.es_client, actions)

        self.es_client.indices.refresh(index=index_name)

        return success

    def search(
        self, index_name: str, query: str, k: int = 20
    ) -> list[ElasticSearchResponse]:
        """
        Search the documents relevant to the query.

        Args:
            index_name (str): Name of the index to search
            query (str): Query to search
            k (int): Number of documents to return

        Returns:
            list[ElasticSearchResponse]: List of ElasticSearch response objects.
        """
        logger.debug("Index: %s - Query: %s - k: %s", index_name, query, k)

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
            "size": k,
        }
        response = self.es_client.search(index=index_name, body=search_body)

        return [
            ElasticSearchResponse(
                doc_id=hit["_source"]["doc_id"],
                content=hit["_source"]["content"],
                contextualized_content=hit["_source"]["contextualized_content"],
                score=hit["_score"],
            )
            for hit in response["hits"]["hits"]
        ]
