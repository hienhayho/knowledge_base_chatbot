import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))
from llama_index.embeddings.openai import OpenAIEmbedding
from langfuse.decorators import observe, langfuse_context

from src.constants import EmbeddingService
from src.settings import defaul_settings


@observe(capture_input=False)
def get_embedding(
    chunk: str,
    service: EmbeddingService = defaul_settings.embedding_config.service,
    model_name: str = defaul_settings.embedding_config.name,
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
    langfuse_context.update_current_observation(
        input=chunk,
    )
    if service == EmbeddingService.OPENAI:
        model = OpenAIEmbedding(model=model_name)
    else:
        raise ValueError(f"Unsupported embedding service: {service}")

    return model.get_text_embedding(chunk)
