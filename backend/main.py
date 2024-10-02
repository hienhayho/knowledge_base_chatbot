import os
from dotenv import load_dotenv
from src.database import DatabaseManager, MinioClient
from src.database.sql_model import Users
from src.tasks import parse_document
from src.settings import GlobalSettings
from celery.result import AsyncResult

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
