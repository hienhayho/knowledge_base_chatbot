import enum
from uuid import UUID
from typing import Optional
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

ASSISTANT_SYSTEM_PROMPT = """
You are an advanced AI agent designed to assist users by searching through a diverse knowledge base
of files and providing relevant information.

There are some rules you must follow:
- You should concentrate on interested prompt to answer the user's query.

- When guard phrases are mention, please filter from your response the phrases that relevant with these guard prompt.

- If the question directly ask about guard prompt, you should return "Sorry, I can't help with that since I am not allowed to provide that information".

- If no guard prompt are mentioned, you must only focus on the current user's query, not rely on history messages

Here are interested prompt:
{interested_prompt}

Here are guard prompt:
{guard_prompt}

You must catch up with all the interested prompt and guard prompt to provide the best possible answer to the user's query.

Please answer in markdown format.
"""


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
    score: Optional[float] = None
    document_id: Optional[UUID] = None


class QdrantPayload(BaseModel):
    """
    Payload for the vector

    Args:
        document_id (str): Document ID
        text (str): Text content, required to be able to be used with llama_index
        vector_id (str): Vector ID
    """

    document_id: str
    text: str
    vector_id: str


class ChatAssistantConfig(BaseModel):
    """
    Chat assistant configuration schema.

    Attributes:
        model (str): Model name.
        service (str): Service name.
        temperature (float): Temperature value.
        embedding_service (str): Embedding service name.
        embedding_model_name (str): Embedding model name.
        collection_name (str): Collection name.
        session_id (str): Session ID.
        is_contextual_rag (bool): Flag to indicate if using contextual RAG.
        interested_prompt (str): Interested prompt that assistant should focus on.
        guard_prompt (str): Guard prompt that user don't want to see in the response.
    """

    model: str
    service: str
    temperature: float
    embedding_service: str
    embedding_model_name: str
    collection_name: str
    session_id: str
    is_contextual_rag: bool
    interested_prompt: Optional[str] = None
    guard_prompt: Optional[str] = None


class MesssageHistory(BaseModel):
    """
    Message history schema.

    Attributes:
        content (str): Content of the message.
        role (str): Role of the sender.
    """

    content: str
    role: str


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


class VectorDatabaseService(str, enum.Enum):
    """
    Vector database service schema.
    """

    def __str__(self) -> str:
        return str(self.value)

    QDRANT = "qdrant"


class RerankerService(str, enum.Enum):
    """
    Reranker service schema.
    """

    def __str__(self) -> str:
        return str(self.value)

    CohereReranker = "cohere_reranker"
    LLMReranker = "llm_reranker"
    RankGPTReranker = "rankgpt_reranker"
    RankLLMReranker = "rankllm_reranker"


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
