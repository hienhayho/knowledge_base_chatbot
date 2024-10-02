from abc import ABC, abstractmethod
from typing import List, Dict, Any


class BaseVectorDatabase(ABC):
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
