import sys
from pathlib import Path
from abc import ABC, abstractmethod
from typing import List, Dict, Any

sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from pydantic import BaseModel
from qdrant_client.http import models
from qdrant_client import QdrantClient
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


class QdrantPayload(BaseModel):
    """
    Payload for the vector

    Args:
        file_path (str): File path saved in Minio's bucket (Object name)
    """

    file_path: str


class QdrantVectorDatabase(BaseVectorDatabase):
    """
    Qdrant client to index and search vectors for contextual RAG.
    """

    def __init__(
        self, url: str, distance: models.Distance = models.Distance.COSINE
    ) -> None:
        """
        Initialize the Qdrant client.

        Args:
            url (str): URL of the Qdrant server
            distance (Distance): Distance metric to use. Default is `COSINE`
        """
        self.url = url
        self.client = QdrantClient(url)
        self.distance = distance

        logger.info("Qdrant client initialized successfully !!!")

    def check_collection_exists(self, collection_name: str):
        return self.client.collection_exists(collection_name)

    def create_collection(self, collection_name: str, vector_size: int):
        if not self.client.collection_exists(collection_name):
            logger.info(f"Creating collection {collection_name} ...")
            self.client.create_collection(
                collection_name,
                vectors_config=models.VectorParams(
                    size=vector_size, distance=self.distance
                ),
            )

        else:
            logger.info(f"Collection {collection_name} already exists !!!")

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
        if not self.client.collection_exists(collection_name):
            self.create_collection(collection_name, len(vector))

        self.client.upsert(
            collection_name=collection_name,
            points=[
                models.PointStruct(
                    id=vector_id,
                    payload=payload,
                    vector=vector,
                )
            ],
        )

        logger.info(f"Collection: {collection_name} - Vector: {vector_id}")
