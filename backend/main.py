from src.agents import ContextualRAGAgent
from src.settings import defaul_settings

rag = ContextualRAGAgent(
    setting=defaul_settings, collection_name="e21f3b17-9169-4024-9637-975051e5cb2c"
)

print(rag.chat("What is workflow generation of ChainBuddy ?"))
