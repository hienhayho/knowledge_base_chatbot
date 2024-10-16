minio_config = dict(
    upload_bucket_name="uploads",
    secure=False,
)

temp_folder = "uploads"

embeddings_config = dict(
    service="openai", model="text-embedding-3-small", chunk_size=2048
)

llm_config = dict(service="openai", model="gpt-4o-mini")

contextual_rag_config = dict(
    semantic_weight=0.8,
    bm25_weight=0.2,
    vector_database_service="qdrant",
    reranker_service="rankgpt_reranker",
    top_k=150,
    top_n=3,
)

agent_config = dict(
    type="openai",
)
