from dotenv import load_dotenv
from llama_index.core import VectorStoreIndex, StorageContext
from llama_index.vector_stores.qdrant import QdrantVectorStore

import qdrant_client

load_dotenv()

client = qdrant_client.QdrantClient(host="localhost", port=6333)
vector_store = QdrantVectorStore(
    client=client, collection_name="5e642498-af9a-490e-b92d-ea3b084bf5d3"
)

storage_context = StorageContext.from_defaults(vector_store=vector_store)

index = VectorStoreIndex.from_vector_store(
    vector_store, storage_context=storage_context
)

query_engine = index.as_query_engine()

print(query_engine.query("What is A SCANDAL IN BOHEMIA ?"))
