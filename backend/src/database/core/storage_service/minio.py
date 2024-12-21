import os
import sys
import logging
from minio import Minio
from pathlib import Path
from urllib3.exceptions import MaxRetryError
from tenacity import retry, stop_after_attempt, wait_fixed, after_log, before_sleep_log

sys.path.append(str(Path(__file__).parent.parent.parent.parent))
from .base import BaseStorageClient
from src.utils import get_formatted_logger, convert_boolean_env_var

logger = get_formatted_logger(__file__)


def get_minio_client() -> "MinioClient":
    return MinioClient.get_instance(
        url=os.getenv("MINIO_URL"),
        access_key=os.getenv("MINIO_ACCESS_KEY"),
        secret_key=os.getenv("MINIO_SECRET_KEY"),
        secure=convert_boolean_env_var("MINIO_SECURE"),
    )


class MinioClient(BaseStorageClient):
    """
    Minio client to interact with Minio server
    """

    @retry(
        reraise=True,
        stop=stop_after_attempt(4),
        wait=wait_fixed(4),
        after=after_log(logger, logging.DEBUG),
        before_sleep=before_sleep_log(logger, logging.DEBUG),
    )
    def __init__(
        self, url: str, access_key: str, secret_key: str, secure: bool = False
    ):
        """
        Initialize Minio client

        Args:
            url (str): Minio url
            access_key (str): Minio access key - **MINIO_ROOT_USER** (docker-compose.yml)
            secret_key (str): Minio secret key - **MINIO_ROOT_PASSWORD** (docker-compose.yml)
            secure (bool): Enable secure connection
        """

        self.client = Minio(
            endpoint=url, access_key=access_key, secret_key=secret_key, secure=secure
        )
        self.test_connection()
        logger.info("MinioClient initialized successfully !!!")

    def get_upload_bucket_name(self):
        """
        Get the upload bucket name
        """
        return os.getenv("MINIO_UPLOAD_BUCKET_NAME")

    @classmethod
    def get_instance(
        cls,
        url: str,
        access_key: str,
        secret_key: str,
        secure: bool = False,
    ) -> "MinioClient":
        """
        Get Minio client instance

        Args:
            url (str): Minio url
            access_key (str): Minio access key
            secret_key (str): Minio secret key
            secure (bool): Enable secure connection

        Returns:
            MinioClient: Minio client instance
        """
        return cls(url, access_key, secret_key, secure)

    def test_connection(self):
        """
        Test the connection with the Minio server by listing buckets
        """
        try:
            self.client.list_buckets()
        except MaxRetryError:
            raise ConnectionError("Minio connection failed")

    def check_bucket_exists(self, bucket_name: str) -> bool:
        """
        Check if bucket exists in Minio

        Args:
            bucket_name (str): Bucket name

        Returns:
            bool: True if bucket exists, False otherwise
        """
        return self.client.bucket_exists(bucket_name)

    def create_bucket(self, bucket_name: str) -> None:
        """
        Create bucket in Minio

        Args:
            bucket_name (str): Bucket name
        """
        self.client.make_bucket(bucket_name)
        logger.info(f"Bucket {bucket_name} created successfully !!!")

    @retry(stop=stop_after_attempt(3))
    def upload_file(
        self, bucket_name: str, object_name: str, file_path: str | Path
    ) -> None:
        """
        Upload file to Minio

        Args:
            bucket_name (str): Bucket name
            object_name (str): Object name to save in Minio
            file_path (str | Path): Local file path to be uploaded
        """
        file_path = str(file_path)

        if not self.check_bucket_exists(bucket_name):
            logger.debug(f"Bucket {bucket_name} does not exist. Creating bucket...")
            self.create_bucket(bucket_name)

        self.client.fput_object(
            bucket_name=bucket_name, object_name=object_name, file_path=file_path
        )
        logger.info(f"Uploaded: {file_path} --> {bucket_name}/{object_name}")

    def download_file(self, bucket_name: str, object_name: str, file_path: str):
        """
        Download file from Minio

        Args:
            bucket_name (str): Bucket name
            object_name (str): Object name to download
            file_path (str): File path to save
        """
        if not self.check_bucket_exists(bucket_name):
            logger.warning(f"Bucket {bucket_name} does not exist. Do nothing ...")
            return

        self.client.fget_object(
            bucket_name=bucket_name, object_name=object_name, file_path=file_path
        )
        logger.info(f"Downloaded: {bucket_name}/{object_name} --> {file_path}")

    def remove_file(self, bucket_name: str, object_name: str) -> None:
        """
        Remove file from Minio

        Args:
            bucket_name (str): Bucket name
            object_name (str): Object name to remove
        """
        if not self.check_bucket_exists(bucket_name):
            logger.warning(f"Bucket {bucket_name} does not exist. Do nothing ...")
            return

        self.client.remove_object(bucket_name=bucket_name, object_name=object_name)
        logger.debug(f"Removed from minio: {bucket_name}/{object_name}")

    def remove_bucket(self, bucket_name: str) -> None:
        """
        Remove bucket from Minio

        Args:
            bucket_name (str): Bucket name
        """
        if not self.check_bucket_exists(bucket_name):
            logger.warning(f"Bucket {bucket_name} does not exist. Cannot remove ...")
            return

        files = self.client.list_objects(bucket_name, recursive=True)
        if files:
            logger.warning(f"Bucket {bucket_name} is not empty. Removing all files ...")
            for file in files:
                self.client.remove_object(bucket_name, file.object_name)

        self.client.remove_bucket(bucket_name)
        logger.info(f"Removed bucket: {bucket_name}")
