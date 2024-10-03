import os
import qdrant_client
from dotenv import load_dotenv
from llama_index.core import VectorStoreIndex, StorageContext, Settings
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.embeddings.openai import OpenAIEmbedding

load_dotenv()

client = qdrant_client.QdrantClient(
    os.getenv("QDRANT_URL"),
)

Settings.embed_model = OpenAIEmbedding()

vector_store = QdrantVectorStore(
    client=client,
    collection_name="205380b9-90e9-4a14-818c-72d566d9093c",
)

storage_context = StorageContext.from_defaults(vector_store=vector_store)

index = VectorStoreIndex.from_vector_store(
    vector_store=vector_store,
    storage_context=storage_context,
    embed_model=Settings.embed_model,
)

query_engine = index.as_query_engine()

print(query_engine.query("ChainBuddy là gì ? Chi tiết"))
