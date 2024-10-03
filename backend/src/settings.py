import os
from mmengine import Config
from typing import Optional
from dotenv import load_dotenv
from pydantic import BaseModel, Field

load_dotenv()

config = Config.fromfile("config.py")


class APIKeys(BaseModel):
    """
    API keys configuration.

    Attributes:
        OPENAI_API_KEY (Optional[str]): OpenAI API key
        LLAMA_PARSE_API_KEY (Optional[str]): LlamaParse API key for parsing .pdf files
        COHERE_API_KEY (Optional[str]): Cohere API key for reranking
    """

    OPENAI_API_KEY: Optional[str] = None
    LLAMA_PARSE_API_KEY: Optional[str] = None
    COHERE_API_KEY: Optional[str] = None


class MinioConfig(BaseModel):
    """
    Minio configuration.

    Attributes:
        url (Optional[str]): Minio url
        access_key (Optional[str]): Minio access key
        secret_key (Optional[str]): Minio secret key
        secure (bool): Enable secure connection
    """

    url: Optional[str] = None
    access_key: Optional[str] = None
    secret_key: Optional[str] = None
    secure: bool = False


class SQLConfig(BaseModel):
    """
    SQL configuration.

    Attributes:
        url (Optional[str]): SQL database url
    """

    url: Optional[str] = None


class QdrantConfig(BaseModel):
    """
    Qdrant configuration.

    Attributes:
        url (Optional[str]): Qdrant url
    """

    url: Optional[str] = None


class ElasticSearchConfig(BaseModel):
    """
    ElasticSearch configuration.

    Attributes:
        url (Optional[str]): ElasticSearch url
    """

    url: Optional[str] = None


class EmbeddingConfig(BaseModel):
    """
    Embedding configuration.

    Attributes:
        chunk_size (int): Embedding chunk size
        service (str): Embedding service
        model_name (str): Embedding model
    """

    chunk_size: int
    service: str
    name: str


class LLMConfig(BaseModel):
    """
    LLM configuration.

    Attributes:
        service (str): LLM service
        model_name (str): LLM model name
    """

    service: str
    name: str


class GlobalSettings(BaseModel):
    """
    Global settings.

    Attributes:
        api_keys (APIKeys): API keys configuration
        minio_config (MinioConfig): Minio configuration
        sql_config (SQLConfig): SQL configuration
        qdrant_config (QdrantConfig): Qdrant configuration
        upload_bucket_name (str): Upload bucket name
        embedding_config (EmbeddingConfig): Embedding configuration
        llm_config (LLMConfig): LLM configuration
    """

    api_keys: APIKeys = Field(
        default=APIKeys(
            OPENAI_API_KEY=os.getenv("OPENAI_API_KEY"),
            LLAMA_PARSE_API_KEY=os.getenv("LLAMA_PARSE_API_KEY"),
            COHERE_API_KEY=os.getenv("COHERE_API_KEY"),
        ),
        description="API keys configuration",
    )

    minio_config: MinioConfig = Field(
        default=MinioConfig(
            url=os.getenv("MINIO_URL"),
            access_key=os.getenv("MINIO_ACCESS_KEY"),
            secret_key=os.getenv("MINIO_SECRET_KEY"),
            secure=config.minio_config.secure,
        ),
        description="Minio configuration",
    )

    sql_config: SQLConfig = Field(
        default=SQLConfig(
            url=os.getenv("SQL_DB_URL"),
        ),
        description="SQL Database configuration",
    )

    qdrant_config: QdrantConfig = Field(
        default=QdrantConfig(
            url=os.getenv("QDRANT_URL"),
        ),
        description="Qdrant configuration",
    )

    elastic_search_config: ElasticSearchConfig = Field(
        default=ElasticSearchConfig(
            url=os.getenv("ELASTIC_SEARCH_URL"),
        ),
        description="ElasticSearch configuration",
    )

    upload_bucket_name: str = Field(default=config.minio_config.upload_bucket_name)
    upload_temp_folder: str = Field(
        default="uploads", description="Temporary upload folder before moving to Minio"
    )

    embedding_config: EmbeddingConfig = Field(
        default=EmbeddingConfig(
            chunk_size=config.embeddings_config.chunk_size,
            service=config.embeddings_config.service,
            name=config.embeddings_config.model,
        ),
        description="Embedding configuration",
    )

    llm_config: LLMConfig = Field(
        default=LLMConfig(
            service=config.llm_config.service,
            name=config.llm_config.model,
        ),
        description="LLM configuration",
    )


defaul_settings = GlobalSettings()


def get_default_setting():
    """
    Get default settings
    """
    return defaul_settings
