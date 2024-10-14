import sys
import logging
from uuid import UUID
from pathlib import Path
from abc import ABC, abstractmethod
from qdrant_client.http import models
from qdrant_client import QdrantClient
from typing import List, Dict, Any, Optional
from qdrant_client.http.exceptions import ResponseHandlingException
from tenacity import (
    retry,
    stop_after_attempt,
    wait_fixed,
    after_log,
    before_sleep_log,
    retry_if_exception_type,
)

sys.path.append(str(Path(__file__).parent.parent.parent))

from src.constants import QdrantPayload
from src.utils import get_formatted_logger

logger = get_formatted_logger(__file__)


class BaseVectorDatabase(ABC):
    @abstractmethod
    def check_collection_exists(self, collection_name: str):
        """
        Check if the collection exists

        Args:
            collection_name (str): Collection name to check
        """
        pass

    @abstractmethod
    def test_connection(self):
        """
        Test the connection with the server.
        """
        pass

    @abstractmethod
    def create_collection(self, collection_name: str, vector_size: int):
        """
        Create a new collection

        Args:
            collection_name (str): Collection name
            vector_size (int): Vector size
        """
        pass

    @abstractmethod
    def add_vector(
        self,
        collection_name: str,
        vector_id: str,
        vector: List[float],
        payload: Dict[str, Any],
    ):
        """
        Add a vector to the collection

        Args:
            collection_name (str): Collection name to add
            vector_id (str): Vector ID
            vector (List[float]): Vector embedding
            payload (Dict[str, Any]): Payload for the vector
        """
        pass


class QdrantVectorDatabase(BaseVectorDatabase):
    """
    QdrantVectorDatabase client
    """

    @retry(
        reraise=True,
        stop=stop_after_attempt(5),
        wait=wait_fixed(5),
        after=after_log(logger, logging.DEBUG),
        before_sleep=before_sleep_log(logger, logging.DEBUG),
        retry=retry_if_exception_type(ConnectionError),
    )
    def __init__(self, url: str, distance: str = models.Distance.COSINE) -> None:
        self.url = url
        self.client = QdrantClient(url)
        self.distance = distance
        self.test_connection()

        logger.info("Qdrant client initialized successfully !!!")

    def test_connection(self):
        """
        Test the connection with the Qdrant server.
        """
        try:
            self.client.get_collections()
        except ResponseHandlingException:
            raise ConnectionError("Qdrant connection failed")

    def check_collection_exists(self, collection_name: str):
        return self.client.collection_exists(collection_name)

    def create_collection(self, collection_name: str, vector_size: int):
        if not self.client.collection_exists(collection_name):
            logger.info(f"Creating collection {collection_name}")
            self.client.create_collection(
                collection_name,
                vectors_config=models.VectorParams(
                    size=vector_size, distance=self.distance
                ),
            )

    def add_vector(
        self,
        collection_name: str,
        vector_id: str,
        vector: List[float],
        payload: QdrantPayload,
    ):
        """
        Add a vector to the collection

        Args:
            collection_name (str): Collection name to add
            vector_id (str): Vector ID
            vector (List[float]): Vector embedding
            payload (QdrantPayload): Payload for the vector
        """
        if not self.check_collection_exists(collection_name):
            self.create_collection(collection_name, len(vector))

        self.client.upsert(
            collection_name=collection_name,
            points=[
                models.PointStruct(
                    id=vector_id,
                    payload=payload.model_dump(),
                    vector=vector,
                )
            ],
        )

    def delete_vector(self, collection_name: str, document_id: str | UUID):
        """
        Delete a vector from the collection

        Args:
            collection_name (str): Collection name to delete
            document_id (str | UUID): Document ID to delete
        """
        document_id = str(document_id)

        if not self.check_collection_exists(collection_name):
            logger.debug(f"Collection {collection_name} does not exist")
            return

        logger.debug(
            "collection_name: %s - document_id: %s", collection_name, document_id
        )

        self.client.delete(
            collection_name,
            points_selector=models.FilterSelector(
                filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="document_id",
                            match=models.MatchValue(value=document_id),
                        )
                    ]
                )
            ),
        )

    def delete_collection(self, collection_name: str):
        """
        Delete a collection

        Args:
            collection_name (str): Collection name to delete
        """
        if not self.check_collection_exists(collection_name):
            logger.debug(f"Collection {collection_name} does not exist")
            return

        success = self.client.delete_collection(collection_name)

        if success:
            logger.debug(f"Collection {collection_name} deleted successfully!")

    def migrate_collection(
        self, source_collection: str, target_collection: str, batch_size: int = 100
    ):
        """
        Migrate all data from source collection to target collection.

        Args:
            source_collection (str): Name of the source collection
            target_collection (str): Name of the target collection
            batch_size (int): Number of points to process in each batch
        """
        if not self.check_collection_exists(source_collection):
            logger.debug(f"Source collection: {source_collection} does not exist")
            return

        assert self.check_collection_exists(
            target_collection
        ), f"Target collection: {target_collection} does not exist"

        offset: Optional[str] = None

        while True:
            response = self.client.scroll(
                collection_name=source_collection,
                limit=batch_size,
                offset=offset,
                with_payload=True,
                with_vectors=True,
            )

            points = response[0]
            if not points:
                break

            points_to_be_indexed = [
                models.PointStruct(
                    id=point.id,
                    payload=point.payload,
                    vector=point.vector,
                )
                for point in points
            ]

            self.client.upsert(
                collection_name=target_collection, points=points_to_be_indexed
            )

            offset = response[1]
            if offset is None:
                break

        self.delete_collection(source_collection)

        logger.info(
            f"Migration from {source_collection} to {target_collection} completed successfully!"
        )
