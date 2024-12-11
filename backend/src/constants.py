import enum
from uuid import UUID
from pathlib import Path
from typing import Dict
from llama_index.core.bridge.pydantic import BaseModel

DOWNLOAD_FOLDER = Path("downloads")

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

# CONTEXTUAL_PROMPT = """<document>
# {WHOLE_DOCUMENT}
# </document>
# Here is the chunk we want to situate within the whole document
# <chunk>
# {CHUNK_CONTENT}
# </chunk>
# Please give a short succinct context to situate this chunk within the overall document for the purposes of improving search retrieval of the chunk. Answer only with the succinct context and nothing else. Please answer in the source language of the document."""
CONTEXTUAL_PROMPT = """<document>
{WHOLE_DOCUMENT}
</document>
Đây là đoạn văn mà chúng tôi muốn bạn cần đọc
<chunk>
{CHUNK_CONTENT}
</chunk>
bạn hãy cung cấp một ngữ cảnh ngắn gọn và phù hợp để đặt đoạn văn này trong tổng thể tài liệu nhằm cải thiện khả năng tìm kiếm và truy xuất đoạn văn. Chỉ trả lời bằng ngữ cảnh ngắn gọn và không thêm gì khác."""

QA_PROMPT = """We have provided context information below.
---------------------
{context_str}"
---------------------
Given this information, please answer the question: {query_str}

Please ONLY return in json format like this:
{{
    "result": ### Your answer here, MUST BE IN MARKDOWN FORMAT
    "is_chat_false": ### You must decide if the answer is true with the context and question provided
}}
"""

ASSISTANT_SYSTEM_PROMPT = """
You are an advanced AI agent designed to assist users by searching through a diverse knowledge base
of files and providing relevant information.

Here are something you should pay attention to:
{instruct_prompt}

If there are any product's link, please provide the link in the response.

Please answer in markdown format.
"""

embedding_dim = {"text-embedding-ada-002": 1536, "text-embedding-3-large": 3072}


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


class QdrantPayload(BaseModel):
    """
    Payload for the vector

    Args:
        document_id (str): Document ID
        text (str): Text content, required to be able to be used with llama_index
        vector_id (str): Vector ID
    """

    document_id: str | UUID
    text: str
    vector_id: str
    kb_id: str | UUID


class ChatAssistantConfig(BaseModel):
    """
    Chat assistant configuration schema.

    Attributes:
        model (str): Model name.
        conversation_id (str): Conversation ID.
        service (str): Service name.
        temperature (float): Temperature value.
        embedding_service (str): Embedding service name.
        embedding_model_name (str): Embedding model name.
        collection_name (str): Collection name.
        session_id (str): Session ID.
        tools (list[str]): List of tools to be used.
        agent_backstory (str): Agent backstory for crewai agent.
        is_contextual_rag (bool): Flag to indicate if using contextual RAG.
        instruct_prompt (str): Instruction prompt for the assistant.
        file_product_path (str): File path for the product file.
    """

    model: str
    conversation_id: str
    service: str
    temperature: float
    embedding_service: str
    embedding_model_name: str
    collection_name: str
    kb_ids: list[str | UUID]
    session_id: str
    tools: Dict[str, str]
    agent_backstory: str
    is_contextual_rag: bool
    instruct_prompt: str
    file_product_path: str | None


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


class UserRole(str, enum.Enum):
    """
    Enum class for user role
    """

    def __str__(self) -> str:
        return str(self.value)

    ADMIN = "admin"
    USER = "user"


class ExistTools(str, enum.Enum):
    """
    Enum class for all existing tools that allow to be used in the assistant system
    """

    KNOWLEDGE_BASE_QUERY = "knowledge_base_query"
    PRODUCT_SEARCH = "product_search"
