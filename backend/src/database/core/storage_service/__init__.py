import os
import sys
from pathlib import Path
from typing import Type
from dotenv import load_dotenv

sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from .minio import MinioClient, get_minio_client  # noqa: F401
from .s3 import S3Client, get_s3_client  # noqa: F401
from .base import BaseStorageClient
from src.constants import StorageService
from src.settings import config

load_dotenv()


def load_storage_service(type: str | None = None) -> Type[BaseStorageClient]:
    """
    Load storage service based on type and setup bucket name

    Args:
        type (str): Storage service type

    Returns:
        Type[BaseStorageClient]: Storage client instance
    """
    if type is None:
        type = config.storage_config.type

    if type == StorageService.S3:
        return S3Client(
            region_name=os.getenv("AWS_REGION"),
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY"),
            aws_secret_access_key=os.getenv("AWS_SECRET_KEY"),
            upload_bucket_name=os.getenv("AWS_BUCKET_NAME"),
        )
    elif type == StorageService.MINIO:
        return MinioClient(
            url=os.getenv("MINIO_URL"),
            access_key=os.getenv("MINIO_ACCESS_KEY"),
            secret_key=os.getenv("MINIO_SECRET_KEY"),
            secure=os.getenv("MINIO_SECURE"),
        )
    else:
        raise ValueError(f"Invalid storage service type: {type}")
