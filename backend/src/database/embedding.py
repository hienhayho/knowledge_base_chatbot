import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
from llama_index.embeddings.openai import OpenAIEmbedding

from src.constants import EmbeddingService


def get_embedding(
    chunk: str, service: EmbeddingService, model_name: str
) -> list[float]:
    """
    Get the embedding of the text chunk using the specified service

    Args:
        chunk (str): Text chunk to get the embedding for
        service (EmbeddingService): The service to use for the embedding
        model_name (str): Embedding model
    Returns:
        list[float]: The embedding of the text chunk
    """
    if service == EmbeddingService.OPENAI:
        model = OpenAIEmbedding(model=model_name)
    else:
        raise ValueError(f"Unsupported embedding service: {service}")

    return model.get_text_embedding(chunk)
