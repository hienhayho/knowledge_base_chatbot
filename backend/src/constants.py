import enum
from llama_index.core.bridge.pydantic import BaseModel

SUPPORTED_FILE_EXTENSIONS = [
    ".pdf",
    ".docx",
    ".html",
    ".txt",
    ".csv",
    ".xlsx",
    ".json",
    # ".pptx",
]


class DocumentStatus(str, enum.Enum):
    """
    Enum class for document status
    """

    PENDING = "pending"
    PROGRESS = "progress"
    SUCCESS = "success"
    FAILED = "failed"


class EmbeddingService(str, enum.Enum):
    """
    Enum class for embedding services
    """

    OPENAI = "openai"
    HUGGINGFACE = "huggingface"


class SenderType(str, enum.Enum):
    """
    Enum class for sender type
    """

    USER = "user"
    ASSISTANT = "assistant"
