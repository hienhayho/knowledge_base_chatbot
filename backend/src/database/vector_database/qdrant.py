import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

from qdrant_client import QdrantClient
from qdrant_client.http import models
from typing import Any, Dict, List
from .base import BaseVectorDatabase

from src.utils import get_formatted_logger
from .embedding import get_embedding

logger = get_formatted_logger(__file__)


class QdrantVectorDatabase(BaseVectorDatabase):
    def __init__(self, url: str, distance: str = models.Distance.COSINE) -> None:
        self.url = url
        self.client = QdrantClient(url)
        self.distance = distance

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
        payload: Dict[str, Any],
    ):
        pass

    def search_vectors(
        self, collection_name: str, query_vector: List[float], limit: int
    ):
        pass
