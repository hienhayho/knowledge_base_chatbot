from dotenv import load_dotenv

from src.settings import defaul_settings
from src.database import ContextualRAG

load_dotenv()

rag = ContextualRAG.from_setting(setting=defaul_settings)


print(
    rag.contextual_rag_search(
        collection_name="115eef94-3e4d-406b-b28c-e24ea0c060db",
        query="ChainBuddy là gì ?",
        debug=True,
    )
)
