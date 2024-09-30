from llama_index.embeddings.openai import OpenAIEmbedding
from src.constants import GlobalConfig
from src.constants import GlobalConfig


def get_embedding(chunk: str, service = GlobalConfig.MODEL.EMBEDDING_SERVICE, model_name = GlobalConfig.MODEL.EMBEDDING_MODEL_NAME):
    if service == 'openai':
        embed_model = OpenAIEmbedding(model=model_name, api_key=GlobalConfig.MODEL.OPENAI_API_KEY)
    else:
        raise ValueError(f"Invalid embedding service: {service}")
    
    return embed_model.get_text_embedding(chunk)