import os
from mmengine import Config
from dotenv import load_dotenv
from pydantic import BaseModel, Field

load_dotenv()

config = Config.fromfile("config.py")


class APIKeys(BaseModel):
    """
    API keys configuration.

    Attributes:
        OPENAI_API_KEY (str): OpenAI API key
        LLAMA_PARSE_API_KEY (str): Llama Parse API key
    """

    OPENAI_API_KEY: str
    LLAMA_PARSE_API_KEY: str


class MinioConfig(BaseModel):
    """
    Minio configuration.

    Attributes:
        url (str): Minio url
        access_key (str): Minio access key
        secret_key (str): Minio secret key
        secure (bool): Enable secure connection
    """

    url: str
    access_key: str
    secret_key: str
    secure: bool


class SQLConfig(BaseModel):
    """
    SQL configuration.

    Attributes:
        url (str): SQL database url
    """

    url: str


class QdrantConfig(BaseModel):
    """
    Qdrant configuration.

    Attributes:
        url (str): Qdrant database url
    """

    url: str


class EmbeddingConfig(BaseModel):
    """
    Embedding configuration.

    Attributes:
        service (str): Embedding service
        model_name (str): Embedding model
    """

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
        description="SQL configuration",
    )

    qdrant_config: QdrantConfig = Field(
        default=QdrantConfig(
            url=os.getenv("QDRANT_URL"),
        ),
        description="Qdrant configuration",
    )

    upload_bucket_name: str = Field(default=config.minio_config.upload_bucket_name)

    embedding_config: EmbeddingConfig = Field(
        default=EmbeddingConfig(
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
