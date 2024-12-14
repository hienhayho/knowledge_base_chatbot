import sys
from uuid import UUID
from pathlib import Path

from llama_index.core.tools import FunctionTool

sys.path.append(str(Path(__file__).parent.parent.parent))
from src.database import ContextualRAG
from src.settings import GlobalSettings


def load_llama_index_kb_tool(
    setting: GlobalSettings,
    kb_ids: list[str | UUID],
    session_id: str | UUID,
    is_contextual_rag: bool = False,
    system_prompt: str = "",
    description: str = "",
) -> FunctionTool:
    contextual_rag = ContextualRAG.from_setting(setting=setting)

    def knowledge_base_query(user_question: str) -> str:
        """
        Query the knowledge base using contextual RAG

        Args:
            user_question (str): Query string

        Returns:
            str: Response from the contextual RAG
        """
        return contextual_rag.search(
            session_id=session_id,
            is_contextual_rag=is_contextual_rag,
            kb_ids=[str(kb_id) for kb_id in kb_ids],
            query=user_question,
            top_k=setting.contextual_rag_config.top_k,
            system_prompt=system_prompt,
        )

    return FunctionTool.from_defaults(
        fn=knowledge_base_query,
        return_direct=True,
        description=description
        or "Useful tool for querying knowledge base using contextual RAG",
    )
