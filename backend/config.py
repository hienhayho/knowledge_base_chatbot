minio_config = dict(
    upload_bucket_name="uploads",
    secure=False,
)

temp_folder = "uploads"

embeddings_config = dict(
    service="openai", model="text-embedding-3-small", chunk_size=2048
)

llm_config = dict(service="openai", model="gpt-4o-mini")
