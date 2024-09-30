from abc import ABC, abstractmethod
from qdrant_client import QdrantClient
from qdrant_client.http import models
from chromadb import Client as ChromaClient
from typing import List, Dict, Any

DEFAULT_DISTANCE = models.Distance.COSINE


class VectorDB(ABC):
    @abstractmethod
    def create_collection(self, collection_name: str):
        pass

    @abstractmethod
    def add_vector(
        self,
        collection_name: str,
        vector_id: str,
        vector: List[float],
        payload: Dict[str, Any],
    ):
        pass

    @abstractmethod
    def search_vectors(
        self, collection_name: str, query_vector: List[float], limit: int
    ):
        pass


class QdrantVectorDB(VectorDB):
    def __init__(self, url: str, distance: str = DEFAULT_DISTANCE):
        self.client = QdrantClient(url)
        self.distance = distance
        self.initialized_collections = set()
        self.pending_collections = set()

    def create_collection(self, collection_name: str):
        if collection_name not in self.pending_collections:
            self.pending_collections.add(collection_name)

    def _initialize_collection(self, collection_name: str, vector_size: int):
        self.client.recreate_collection(
            collection_name=collection_name,
            vectors_config=models.VectorParams(
                size=vector_size, distance=self.distance
            ),
        )
        self.client.create_payload_index(
            collection_name=collection_name,
            field_name="document_chunk_id",
            field_schema=models.PayloadSchemaType.INTEGER,
        )
        self.initialized_collections.add(collection_name)
        self.pending_collections.remove(collection_name)

    def add_vector(
        self,
        collection_name: str,
        vector_id: str,
        vector: List[float],
        payload: Dict[str, Any],
    ):
        if collection_name not in self.initialized_collections:
            if collection_name not in self.pending_collections:
                self.create_collection(collection_name)

            if collection_name in self.pending_collections:
                self._initialize_collection(collection_name, len(vector))

        self.client.upsert(
            collection_name=collection_name,
            points=[models.PointStruct(id=vector_id, vector=vector, payload=payload)],
        )

    def search_vectors(
        self, collection_name: str, query_vector: List[float], limit: int
    ):
        if collection_name not in self.initialized_collections:
            raise ValueError(f"Collection {collection_name} has not been initialized.")

        search_result = self.client.search(
            collection_name=collection_name, query_vector=query_vector, limit=limit
        )
        return search_result


class ChromaVectorDB(VectorDB):
    def __init__(self, settings):
        self.client = ChromaClient(settings)
        self.collections = {}

    def create_collection(self, collection_name: str):
        if collection_name not in self.collections:
            self.collections[collection_name] = self.client.create_collection(
                name=collection_name
            )

    def add_vector(
        self,
        collection_name: str,
        vector_id: str,
        vector: List[float],
        payload: Dict[str, Any],
    ):
        if collection_name not in self.collections:
            self.create_collection(collection_name)

        self.collections[collection_name].add(
            ids=[vector_id], embeddings=[vector], metadatas=[payload]
        )

    def search_vectors(
        self, collection_name: str, query_vector: List[float], limit: int
    ):
        if collection_name not in self.collections:
            raise ValueError(f"Collection {collection_name} has not been initialized.")

        results = self.collections[collection_name].query(
            query_embeddings=[query_vector], n_results=limit
        )
        return results
