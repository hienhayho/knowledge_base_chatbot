import sys
import time
import uuid
import torch
from uuid import UUID
from tqdm import tqdm
from pathlib import Path
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.http import models
from llama_index.core import (
    Settings,
    Document,
    StorageContext,
    VectorStoreIndex,
)
from langfuse import Langfuse
from langfuse.decorators import langfuse_context, observe
from langfuse.llama_index import LlamaIndexCallbackHandler

from llama_index.llms.openai import OpenAI
from llama_index.core.llms import ChatMessage
from llama_index.core.callbacks import CallbackManager
from llama_index.core.schema import NodeWithScore, Node
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.core.base.embeddings.base import BaseEmbedding
from llama_index.core.node_parser import SemanticSplitterNodeParser
from llama_index.core.llms.function_calling import FunctionCallingLLM

from llama_index.core.postprocessor import LLMRerank
from llama_index.postprocessor.cohere_rerank import CohereRerank
from llama_index.postprocessor.rankllm_rerank import RankLLMRerank
from llama_index.postprocessor.rankgpt_rerank import RankGPTRerank

sys.path.append(str(Path(__file__).parent.parent.parent))

from .utils import get_embedding
from src.utils import get_formatted_logger
from .core import QdrantVectorDatabase
from src.settings import GlobalSettings, default_settings
from src.constants import (
    QA_PROMPT,
    ASSISTANT_SYSTEM_PROMPT,
    LLMService,
    QdrantPayload,
    RerankerService,
    DocumentMetadata,
    EmbeddingService,
    CONTEXTUAL_PROMPT,
)

logger = get_formatted_logger(__file__)
langfuse_callback_handler = LlamaIndexCallbackHandler()
Settings.callback_manager = CallbackManager([langfuse_callback_handler])

load_dotenv()

langfuse = Langfuse()

Settings.chunk_size = default_settings.embedding_config.chunk_size


class ContextualRAG:
    """
    Contextual Retrieval-Augmented Generation (RAG) class to handle the indexing and searching.
    """

    setting: GlobalSettings
    llm: FunctionCallingLLM
    splitter: SemanticSplitterNodeParser
    qdrant_client: QdrantVectorDatabase

    def __init__(self, setting: GlobalSettings):
        """
        Initialize the RAG class with the provided settings.

        Args:
            setting (ConfigSettings): The settings for the RAG.
        """
        self.setting = setting

        embed_model = self.load_embedding_model(
            setting.embedding_config.service, setting.embedding_config.name
        )
        Settings.embed_model = embed_model

        self.llm = self.load_model(
            service=setting.llm_config.service,
            model_name=setting.llm_config.name,
        )
        Settings.llm = self.llm

        self.splitter = SemanticSplitterNodeParser(
            buffer_size=1, breakpoint_percentile_threshold=95, embed_model=embed_model
        )

        self.reranker = self.load_reranker(
            setting.contextual_rag_config.reranker_service,
            top_n=setting.contextual_rag_config.top_n,
        )

        self.qdrant_client = QdrantVectorDatabase(
            url=setting.qdrant_config.url,
        )

        logger.info("ContextualRAG initialized successfully !!!")

    @classmethod
    def from_setting(cls, setting: GlobalSettings) -> "ContextualRAG":
        """
        Create an instance of the ContextualRAG from the settings.

        Args:
            setting (GlobalSettings): The settings for the ContextualRAG.

        Returns:
            ContextualRAG: The instance of the ContextualRAG.
        """
        return cls(setting)

    def load_embedding_model(self, service: str, model_name: str) -> BaseEmbedding:
        """
        Load the embedding model.

        Args:
            service (str): The service to use.
            model_name (str): The model name.

        Returns:
            BaseEmbedding: Embedding model.
        """
        if service == EmbeddingService.OPENAI:
            return OpenAIEmbedding(model=model_name)
        else:
            raise ValueError("Unsupported service")

    def load_model(
        self, service: str, model_name: str, system_prompt: str | None = None
    ) -> FunctionCallingLLM:
        """
        Load LLM model.

        Args:
            service (str): The service to use.
            model_name (str): The model name.
            system_prompt (str | None): The system prompt. Default to `None`.

        Returns:
            FunctionCallingLLM: The loaded LLM model.
        """
        if service == LLMService.OPENAI:
            return OpenAI(model=model_name, system_prompt=system_prompt)
        else:
            raise ValueError("Unsupported service")

    def load_reranker(self, reranker_service: RerankerService, top_n: int = 3):
        """
        Load the reranker only used for the contextualRAG.
        """
        logger.info("Loading reranker: %s", reranker_service)

        supported_rerankers = [e.value for e in RerankerService]

        if reranker_service == RerankerService.CohereReranker:
            assert (
                self.setting.api_keys.COHERE_API_KEY is not None
            ), "COHERE_API_KEY is required for CohereReranker."

            return CohereRerank(
                top_n=top_n, api_key=self.setting.api_keys.COHERE_API_KEY
            )

        elif reranker_service == RerankerService.LLMReranker:
            return LLMRerank(top_n=top_n, choice_batch_size=5)

        elif reranker_service == RerankerService.RankGPTReranker:
            return RankGPTRerank(
                llm=self.llm,
                top_n=top_n,
            )

        elif reranker_service == RerankerService.RankLLMReranker:
            assert torch.cuda.is_available(), "GPU is required for RankLLMReranker."
            return RankLLMRerank(
                llm=self.llm,
                top_n=top_n,
            )

        else:
            raise ValueError(
                f"Unsupported reranker: {reranker_service}. Please choose from: {supported_rerankers}"
            )

    def split_document(
        self,
        document: Document | list[Document],
        document_id: uuid.UUID,
        show_progress: bool = True,
    ) -> list[list[Document]]:
        """
        Split the document into chunks.

        Args:
            document (Document | list[Document]): The document to split.
            show_progress (bool): Show the progress bar.

        Returns:
            list[list[Document]]: List of documents after splitting.
        """
        if isinstance(document, Document):
            document = [document]

        assert isinstance(document, list)

        documents: list[list[Document]] = []

        document = tqdm(document, desc="Splitting...") if show_progress else document

        for doc in document:
            # get random uuid for vector_id
            vector_id = str(uuid.uuid4())
            nodes = self.splitter.get_nodes_from_documents([doc])
            documents.append(
                [
                    Document(
                        text=node.get_content(),
                        metadata={"document_id": document_id, "vector_id": vector_id},
                    )
                    for node in nodes
                ]
            )

        return documents

    def add_contextual_content(
        self,
        origin_document: Document,
        splited_documents: list[Document],
    ) -> tuple[list[Document], list[DocumentMetadata]]:
        """
        Add contextual content to the splited documents.

        Args:
            origin_document (Document): The original document.
            splited_documents (list[Document]): The splited documents from the original document.

        Returns:
            (tuple[list[Document], list[DocumentMetadata]]): Tuple of contextual documents and its metadata.
        """

        whole_document = origin_document.text
        documents: list[Document] = []
        documents_metadata: list[DocumentMetadata] = []

        for chunk in splited_documents:
            messages = [
                ChatMessage(
                    role="system",
                    content="You are a helpful assistant.",
                ),
                ChatMessage(
                    role="user",
                    content=CONTEXTUAL_PROMPT.format(
                        WHOLE_DOCUMENT=whole_document, CHUNK_CONTENT=chunk.text
                    ),
                ),
            ]

            response = self.llm.chat(messages)
            contextualized_content = response.message.content

            # Prepend the contextualized content to the chunk
            new_chunk = contextualized_content + "\n\n" + chunk.text
            # new_chunk = chunk.text

            # Manually generate a doc_id for indexing in elastic search
            documents.append(
                Document(
                    text=new_chunk,
                    metadata=dict(
                        vector_id=chunk.metadata["vector_id"],
                    ),
                ),
            )
            documents_metadata.append(
                DocumentMetadata(
                    vector_id=chunk.metadata["vector_id"],
                    original_content=whole_document,
                    contextualized_content=contextualized_content,
                    # contextualized_content="",
                ),
            )

        return documents, documents_metadata

    def get_contextual_documents(
        self, raw_documents: list[Document], splited_documents: list[list[Document]]
    ) -> tuple[list[Document], list[DocumentMetadata]]:
        """
        Get the contextual documents from the raw and splited documents.

        Args:
            raw_documents (list[Document]): List of raw documents.
            splited_documents (list[list[Document]]): List of splited documents from the raw documents one by one.

        Returns:
            (tuple[list[Document], list[DocumentMetadata]]): Tuple of contextual documents and its metadata.
        """

        documents: list[Document] = []
        documents_metadata: list[DocumentMetadata] = []

        assert len(raw_documents) == len(splited_documents)

        for raw_document, splited_document in tqdm(
            zip(raw_documents, splited_documents),
            desc="Adding contextual content ...",
            total=len(raw_documents),
        ):
            document, metadata = self.add_contextual_content(
                raw_document, splited_document
            )
            documents.extend(document)
            documents_metadata.extend(metadata)

        # return splited_documents, documents_metadata

        return documents, documents_metadata

    def qdrant_insert_data(
        self,
        kb_id: str | UUID,
        chunks: list[Document],
        document_id: uuid.UUID,
        show_progress: bool = True,
    ):
        """
        Insert data to the QdrantVectorStore.
        """
        chunks = tqdm(chunks, desc="Inserting data ...") if show_progress else chunks
        for doc in chunks:
            self.qdrant_client.add_vector(
                collection_name=self.setting.global_vector_db_collection_name,
                vector=get_embedding(doc.text),
                vector_id=doc.metadata["vector_id"],
                payload=QdrantPayload(
                    document_id=str(document_id),
                    text=doc.text,
                    kb_id=kb_id,
                    vector_id=doc.metadata["vector_id"],
                ),
            )

    def get_qdrant_vector_store_index(
        self, client: QdrantClient, collection_name: str
    ) -> VectorStoreIndex:
        """
        Get the QdrantVectorStoreIndex from the QdrantVectorStore.

        Args:
            client (QdrantClient): The Qdrant client.
            collection_name (str): The collection name.

        Returns:
            VectorStoreIndex: The VectorStoreIndex from the QdrantVectorStore.
        """
        logger.info("collection_name: %s", collection_name)

        vector_store = QdrantVectorStore(client=client, collection_name=collection_name)
        storage_context = StorageContext.from_defaults(vector_store=vector_store)

        return VectorStoreIndex.from_vector_store(
            vector_store=vector_store, storage_context=storage_context
        )

    @observe(capture_input=False)
    def rag_search(
        self,
        collection_name: str,
        query: str,
        session_id: str | uuid.UUID,
    ) -> str:
        """
        Search the query with the RAG.

        Args:
            collection_name (str): The qdrant collection name.
            query (str): The query to search.

        Returns:
            str: The search results.
        """
        logger.info("collection_name: %s - query: %s", collection_name, query)

        langfuse_context.update_current_observation(
            input=query, session_id=str(session_id)
        )

        langfuse_callback_handler.set_trace_params(
            session_id=str(session_id),
        )

        index = self.get_qdrant_vector_store_index(
            self.qdrant_client.client, collection_name=collection_name
        )

        query_engine = index.as_query_engine()

        response = query_engine.query(query)

        langfuse.flush()

        return response

    @observe(capture_input=False)
    def contextual_rag_search(
        self,
        kb_ids: list[str],
        query: str,
        session_id: str | uuid.UUID,
        top_k: int = 150,
        system_prompt: str = ASSISTANT_SYSTEM_PROMPT,
    ) -> str:
        """
        Search the query with the Contextual RAG.

        Args:
            collection_name (str): The qdrant collection name (knowledge_bases.id).
            query (str): The query to search.
            session_id (str | uuid.UUID): The session ID (messages.id) to check cost in langfuse.
            top_k (int): The top K documents to retrieve. Default to `150`.
            top_n (int): The top N documents to return after reranking. Default to `3`.
            debug (bool): debug mode.

        Returns:
            str: The search results.
        """
        print(kb_ids)
        start_time = time.time()

        langfuse_callback_handler.set_trace_params(
            session_id=str(session_id),
        )

        logger.debug("Semantic search ...")
        while True:
            semantic_results = self.qdrant_client.search_vector(
                collection_name=self.setting.global_vector_db_collection_name,
                vector=get_embedding(query),
                search_params=models.SearchParams(
                    quantization=models.QuantizationSearchParams(
                        ignore=False,
                        rescore=True,
                        oversampling=2.0,
                    )
                ),
                query_filter=models.Filter(
                    should=[
                        models.FieldCondition(
                            key="kb_id", match=models.MatchAny(any=kb_ids)
                        ),
                    ],
                ),
                limit=top_k,
                timeout=30,
            )

            if len(semantic_results.points) > 0:
                break

        combined_nodes: list[NodeWithScore] = [
            NodeWithScore(
                node=Node(text=point.payload["text"]),
                score=point.score,
            )
            for point in semantic_results.points
        ]

        logger.info("combined_nodes: %s", combined_nodes)

        # query_bundle = QueryBundle(query_str=query)

        # logger.debug("Reranking ...")
        # retrieved_nodes = self.reranker.postprocess_nodes(combined_nodes, query_bundle)

        # contexts = [n.node.text for n in retrieved_nodes]
        contexts = [n.node.text for n in combined_nodes]

        logger.info("contexts: %s", contexts)

        logger.debug("Generating response ...")
        messages = [
            ChatMessage(
                role="system",
                content=system_prompt,
            ),
            ChatMessage(
                role="user",
                content=QA_PROMPT.format(
                    context_str="\n\n".join(contexts),
                    query_str=query,
                ),
            ),
        ]

        response = self.llm.chat(messages).message.content

        logger.info("response: %s", response)

        logger.info("Time taken: %s", time.time() - start_time)

        langfuse.flush()

        return response

    @observe()
    def search(
        self,
        session_id: str | uuid.UUID,
        is_contextual_rag: bool,
        kb_ids: list[str | UUID],
        query: str,
        top_k: int = 150,
        system_prompt: str = ASSISTANT_SYSTEM_PROMPT,
    ):
        """
        Search the query with the RAG.

        Args:
            session_id (str | uuid.UUID): The session ID (conversations.id) to check cost in langfuse.
            is_contextual_rag (bool): Is contextual RAG or not.
            collection_name (str): The qdrant collection name (knowledge_bases.id).
            query (str): The query to search.
            top_k (int): The top K documents to retrieve. Default to `50`.
            top_n (int): The top N documents to return after reranking. Default to `3`.
            debug (bool): debug mode.
        """
        langfuse_callback_handler.set_trace_params(
            session_id=str(session_id),
        )

        if is_contextual_rag:
            response = self.contextual_rag_search(
                kb_ids=kb_ids,
                query=query,
                session_id=session_id,
                top_k=top_k,
                system_prompt=system_prompt,
            )
        else:
            logger.warning("Original RAG search is deprecated.")
            response = ""

        return response
