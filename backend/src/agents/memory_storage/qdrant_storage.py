import sys
import uuid
from crewai import Crew
from pathlib import Path
from pydantic import BaseModel
from typing import Any, Dict, List, Optional
from qdrant_client import QdrantClient, models
from crewai.memory.storage.rag_storage import RAGStorage


sys.path.append(str(Path(__file__).parent.parent.parent.parent))
from src.database import get_embedding


class EmbedderConfig(BaseModel):
    provider: str
    config: Dict[str, Any]


class QdrantStorage(RAGStorage):
    """
    Extends Storage to handle embeddings for memory entries using Qdrant.

    """

    def __init__(
        self,
        type,
        url: str,
        vector_size: int,
        distance: str = models.Distance.COSINE,
        quantize: bool = True,
        allow_reset: bool = False,
        embedder_config: EmbedderConfig = None,
        crew: Crew = None,
    ):
        self.url = url
        self.qdrant_config = dict(
            vectors_config=models.VectorParams(
                size=vector_size, distance=distance, on_disk=True
            ),
        )
        self.embedding_config = embedder_config  # Not use self.embedder_config to not shadow the parent class

        if quantize:
            self.qdrant_config.update(
                optimizers_config=models.OptimizersConfigDiff(
                    default_segment_number=5,
                    indexing_threshold=0,
                ),
                quantization_config=models.BinaryQuantization(
                    binary=models.BinaryQuantizationConfig(always_ram=True),
                ),
            )

        super().__init__(type, allow_reset, embedder_config, crew)

    def search(
        self,
        query: str,
        limit: int = 3,
        filter: Optional[dict] = None,
        score_threshold: float = 0,
    ) -> List[Any]:
        embeded_text = get_embedding(
            query,
            service=self.embedding_config.provider,
            model_name=self.embedding_config.config["model"],
        )

        points = self.client.query_points(
            self.type,
            query=embeded_text,
            query_filter=filter,
            limit=limit,
            score_threshold=score_threshold,
        )
        results = [
            {
                "id": point.id,
                "metadata": point.payload["metadata"],
                "context": point.payload["document"],
                "score": point.score,
            }
            for point in points.points
        ]

        return results

    def reset(self) -> None:
        self.client.delete_collection(self.type)

    def _initialize_app(self):
        self.client = QdrantClient(self.url)
        if not self.client.collection_exists(self.type):
            print(f"Creating collection {self.type}")
            self.client.create_collection(
                collection_name=self.type,
                **self.qdrant_config,
            )

    def save(self, value: Any, metadata: Dict[str, Any]) -> None:
        vector = get_embedding(
            value,
            service=self.embedding_config.provider,
            model_name=self.embedding_config.config["model"],
        )
        point = models.PointStruct(
            id=str(uuid.uuid4()),
            vector=vector,
            payload={
                "document": value,
                "metadata": metadata or {},
            },
        )
        self.client.upsert(self.type, points=[point])
