import enum
from uuid import UUID
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

CONTEXTUAL_PROMPT = """<document>
{WHOLE_DOCUMENT}
</document>
Here is the chunk we want to situate within the whole document
<chunk>
{CHUNK_CONTENT}
</chunk>
Please give a short succinct context to situate this chunk within the overall document for the purposes of improving search retrieval of the chunk. Answer only with the succinct context and nothing else."""

QA_PROMPT = (
    "We have provided context information below. \n"
    "---------------------\n"
    "{context_str}"
    "\n---------------------\n"
    "Given this information, please answer the question: {query_str}\n"
)


class DocumentMetadata(BaseModel):
    """
    Document metadata schema.

    Attributes:
        vector_id (UUID): Vector ID in the vector store.
        original_content (str): Original content of the document.
        contextualized_content (str): Contextualized content of the document which will be prepend to the original content.
    """

    vector_id: UUID
    original_content: str
    contextualized_content: str


class ElasticSearchResponse(BaseModel):
    """
    ElasticSearch response schema.

    Attributes:
        doc_id (str): Document ID.
        content (str): Content of the document.
        contextualized_content (str): Contextualized content of the document.
        score (float): Score of the document.
    """

    vector_id: UUID
    content: str
    contextualized_content: str
    score: float


class FileStatus(str, enum.Enum):
    """
    Enum class for file status
    """

    def __str__(self) -> str:
        return str(self.value)

    UPLOADED = "uploaded"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"


class DocumentStatus(str, enum.Enum):
    """
    Enum class for document status
    """

    def __str__(self) -> str:
        return str(self.value)

    PENDING = "pending"
    PROGRESS = "progress"
    SUCCESS = "success"
    FAILED = "failed"


class EmbeddingService(str, enum.Enum):
    """
    Enum class for embedding services
    """

    def __str__(self) -> str:
        return str(self.value)

    OPENAI = "openai"


class SenderType(str, enum.Enum):
    """
    Enum class for sender type
    """

    def __str__(self) -> str:
        return str(self.value)

    USER = "user"
    ASSISTANT = "assistant"


class LLMService(str, enum.Enum):
    """
    LLM service schema.
    """

    def __str__(self) -> str:
        return str(self.value)

    OPENAI = "openai"


class ErrorResponse(BaseModel):
    detail: str


class RAGType(str, enum.Enum):
    """
    Enum class for RAG type
    """

    def __str__(self) -> str:
        return str(self.value)

    CONTEXTUAL = "contextual"
    ORIGIN = "origin"
    BOTH = "both"
