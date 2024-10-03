import os
import sys
import json
import uuid
from tqdm import tqdm
from pathlib import Path
from dotenv import load_dotenv

sys.path.append(str(Path(__file__).parent.parent.parent))

from llama_index.core import (
    Settings,
    Document,
    QueryBundle,
    StorageContext,
    VectorStoreIndex,
)
from qdrant_client import QdrantClient
from llama_index.llms.openai import OpenAI
from llama_index.core.llms import ChatMessage
from llama_index.core.schema import NodeWithScore, Node
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core.base.response.schema import Response
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.core.base.embeddings.base import BaseEmbedding
from llama_index.postprocessor.cohere_rerank import CohereRerank
from llama_index.core.node_parser import SemanticSplitterNodeParser
from llama_index.core.llms.function_calling import FunctionCallingLLM

from .core import ElasticSearch
from src.utils import get_formatted_logger
from src.settings import GlobalSettings, defaul_settings
from src.constants import (
    CONTEXTUAL_PROMPT,
    QA_PROMPT,
    DocumentMetadata,
    LLMService,
    EmbeddingService,
)

logger = get_formatted_logger(__file__)

load_dotenv()

Settings.chunk_size = defaul_settings.embedding_config.chunk_size


class ContextualRAG:
    """
    Contextual Retrieval-Augmented Generation (RAG) class to handle the indexing and searching of Contextual RAG.
    """

    setting: GlobalSettings
    llm: FunctionCallingLLM
    splitter: SemanticSplitterNodeParser
    es: ElasticSearch
    qdrant_client: QdrantClient

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
            service=setting.llm_config.service, model_name=setting.llm_config.name
        )
        Settings.llm = self.llm

        self.splitter = SemanticSplitterNodeParser(
            buffer_size=1, breakpoint_percentile_threshold=95, embed_model=embed_model
        )

        self.es = ElasticSearch(url=setting.elastic_search_config.url)

        self.qdrant_client = QdrantClient(
            url=setting.qdrant_config.url,
        )

        logger.info("ContextualRAG initialized successfully !!!")

    @classmethod
    def from_setting(cls, setting: GlobalSettings) -> "ContextualRAG":
        """
        Create an instance of the ContextualRAG from the settings.

        Args:
            setting (GlobalSettings): The settings for the RAG.

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

    def split_document(
        self,
        document: Document | list[Document],
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
            nodes = self.splitter.get_nodes_from_documents([doc])
            documents.append([Document(text=node.get_content()) for node in nodes])

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

            # Manually generate a doc_id for indexing in elastic search
            doc_id = str(uuid.uuid4())
            documents.append(
                Document(
                    text=new_chunk,
                    metadata=dict(
                        doc_id=doc_id,
                    ),
                ),
            )
            documents_metadata.append(
                DocumentMetadata(
                    doc_id=doc_id,
                    original_content=whole_document,
                    contextualized_content=contextualized_content,
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

        return documents, documents_metadata

    def es_index_document(
        self, index_name: str, documents_metadata: list[DocumentMetadata]
    ):
        """
        Index the documents in the ElasticSearch.

        Args:
            index_name (str): Name of the index to index documents.
            documents_metadata (list[DocumentMetadata]): List of documents metadata to index.
        """
        logger.info(
            "index_name: %s - len(documents_metadata): %s",
            index_name,
            len(documents_metadata),
        )
        self.es.index_documents(
            index_name=index_name, documents_metadata=documents_metadata
        )

    def ingest_data(
        self,
        collection_name: str,
        documents: list[Document],
        show_progress: bool = True,
    ):
        """
        Ingest the data to the QdrantVectorStore.

        Args:
            collection_name (str): The collection name.
            documents (list[Document]): List of documents to ingest.
            show_progress (bool): Show the progress bar.
        """
        logger.info("collection_name: %s", collection_name)

        vector_store = QdrantVectorStore(
            client=self.qdrant_client, collection_name=collection_name
        )

        storage_context = StorageContext.from_defaults(vector_store=vector_store)

        index = VectorStoreIndex.from_documents(
            documents, storage_context=storage_context, show_progress=show_progress
        )

        return index  # noqa

    def insert_data(
        self,
        collection_name: str,
        documents: list[Document],
        show_progress: bool = True,
    ):
        """
        Insert data to the QdrantVectorStore.

        Args:
            collection_name (str): The collection name.
            documents (list[Document]): List of documents to insert.
            show_progress (bool): Show the progress bar.
        """
        logger.info("collection_name: %s", collection_name)

        vector_store = QdrantVectorStore(
            client=self.qdrant_client, collection_name=collection_name
        )

        storage_context = StorageContext.from_defaults(vector_store=vector_store)

        index = VectorStoreIndex.from_vector_store(
            vector_store=vector_store, storage_context=storage_context
        )

        documents = (
            tqdm(documents, desc=f"Inserting data to: {collection_name} ...")
            if show_progress
            else documents
        )
        for document in documents:
            index.insert(document)

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

    def contextual_rag_search(
        self, collection_name: str, query: str, k: int = 150, debug: bool = False
    ) -> str:
        """
        Search the query with the Contextual RAG.

        Args:
            collection_name (str): The qdrant collection name.
            query (str): The query to search.
            k (int): The number of documents to return. Default to `150`.
            debug (bool): debug mode.

        Returns:
            str: The search results.
        """
        logger.info(
            "collection_name: %s - k: %s - query: %s", collection_name, k, query
        )

        bm25_weight = self.setting.contextual_rag_config.bm25_weight
        semantic_weight = self.setting.contextual_rag_config.semantic_weight

        index = self.get_qdrant_vector_store_index(
            self.qdrant_client.client, collection_name=collection_name
        )

        retriever = VectorIndexRetriever(
            index=index,
            similarity_top_k=k,
        )

        query_engine = RetrieverQueryEngine(retriever=retriever)

        semantic_results: Response = query_engine.query(query)
        semantic_doc_id = [
            node.metadata["doc_id"] for node in semantic_results.source_nodes
        ]

        def get_content_by_doc_id(doc_id: str):
            for node in semantic_results.source_nodes:
                if node.metadata["doc_id"] == doc_id:
                    return node.text
            return ""

        bm25_results = self.es.search(query, k=k)
        bm25_doc_id = [result.doc_id for result in bm25_results]

        combined_nodes: list[NodeWithScore] = []
        combined_ids = list(set(semantic_doc_id + bm25_doc_id))

        # Compute score according to: https://github.com/anthropics/anthropic-cookbook/blob/main/skills/contextual-embeddings/guide.ipynb
        semantic_count = 0
        bm25_count = 0
        both_count = 0
        for id in combined_ids:
            score = 0
            content = ""
            if id in semantic_doc_id:
                index = semantic_doc_id.index(id)
                score += semantic_weight * (1 / (index + 1))
                content = get_content_by_doc_id(id)
                semantic_count += 1

            if id in bm25_doc_id:
                index = bm25_doc_id.index(id)
                score += bm25_weight * (1 / (index + 1))

                if content == "":
                    content = (
                        bm25_results[index].contextualized_content
                        + "\n\n"
                        + bm25_results[index].content
                    )
                bm25_count += 1
            if id in semantic_doc_id and id in bm25_doc_id:
                both_count += 1

            combined_nodes.append(
                NodeWithScore(
                    node=Node(
                        text=content,
                    ),
                    score=score,
                )
            )

        if debug:
            logger.info(
                "semantic_count: %s - bm25_count: %s - both_count: %s",
                semantic_count,
                bm25_count,
                both_count,
            )

        reranker = CohereRerank(
            top_n=self.setting.top_n,
            api_key=os.getenv("COHERE_API_KEY"),
        )

        query_bundle = QueryBundle(query_str=query)

        retrieved_nodes = reranker.postprocess_nodes(combined_nodes, query_bundle)

        contexts = [n.node.text for n in retrieved_nodes]

        messages = [
            ChatMessage(
                role="system",
                content="You are a helpful assistant.",
            ),
            ChatMessage(
                role="user",
                content=QA_PROMPT.format(
                    context_str=json.dumps(contexts),
                    query_str=query,
                ),
            ),
        ]

        response = self.llm.chat(messages).message.content

        return response
