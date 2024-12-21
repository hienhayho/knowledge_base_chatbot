storage_config = dict(
    type="s3",
)

temp_folder = "uploads"

embeddings_config = dict(
    service="openai", model="text-embedding-3-large", chunk_size=1024
)

global_vector_db_collection_name = "qdrant_collection"

llm_config = dict(service="openai", model="gpt-4o-mini")

contextual_rag_config = dict(
    semantic_weight=0.8,
    bm25_weight=0.2,
    vector_database_service="qdrant",
    reranker_service="rankgpt_reranker",
    top_k=150,
    top_n=3,
)

agent_config = dict(type="openai", use_agent_memory=False)
