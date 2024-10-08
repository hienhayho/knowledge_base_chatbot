import sys
from uuid import UUID
from pathlib import Path

from llama_index.core.tools import FunctionTool

sys.path.append(str(Path(__file__).parent.parent))
from src.database import ContextualRAG
from src.settings import GlobalSettings


def load_kb_tool(
    setting: GlobalSettings,
    collection_name: str,
    conversation_id: str | UUID,
    is_contextual_rag: bool = False,
) -> FunctionTool:
    contextual_rag = ContextualRAG.from_setting(setting=setting)

    def knowledge_base_query(query: str) -> str:
        """
        Query the knowledge base using contextual RAG

        Args:
            query (str): Query string

        Returns:
            str: Response from the contextual RAG
        """
        return contextual_rag.search(
            session_id=conversation_id,
            is_contextual_rag=is_contextual_rag,
            collection_name=collection_name,
            query=query,
            top_k=setting.contextual_rag_config.top_k,
            top_n=setting.contextual_rag_config.top_n,
            debug=True,
        )

    return FunctionTool.from_defaults(
        fn=knowledge_base_query,
        return_direct=True,
        description="Useful tool for querying knowledge base using contextual RAG",
    )
