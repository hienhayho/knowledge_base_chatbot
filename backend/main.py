from dotenv import load_dotenv
from src.database import (
    DatabaseManager,
    MinioClient,
    QdrantVectorDatabase,
    ElasticSearch,
)
from src.settings import GlobalSettings

load_dotenv()

# task = parse_document.delay("sample/dummy.csv")
# print(task.id)

# while True:
#     result = AsyncResult(task.id)
#     print(result.state)
#     print(result.info)
#     if result.state == "SUCCESS":
#         break

setting = GlobalSettings()

minioClient = MinioClient(
    url=setting.minio_config.url,
    access_key=setting.minio_config.access_key,
    secret_key=setting.minio_config.secret_key,
    secure=setting.minio_config.secure,
)

qdrant_vector_db = QdrantVectorDatabase(
    url=setting.qdrant_config.url,
)
elastic_search_db = ElasticSearch(
    url=setting.elastic_search_config.url,
)

db = DatabaseManager(
    setting.sql_config.url,
    minio_client=minioClient,
    vector_db_client=qdrant_vector_db,
    elastic_search_client=elastic_search_db,
)
