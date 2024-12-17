import os
import sys
import boto3
import logging
from pathlib import Path
from dotenv import load_dotenv
from botocore.exceptions import ClientError
from tenacity import retry, stop_after_attempt, wait_fixed, after_log, before_sleep_log

sys.path.append(str(Path(__file__).parent.parent.parent.parent))
from .base import BaseStorageClient
from src.utils import get_formatted_logger

logger = get_formatted_logger(__file__)

load_dotenv()


def get_s3_client() -> "S3Client":
    return S3Client(
        region_name=os.getenv("AWS_REGION"),
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY"),
        aws_secret_access_key=os.getenv("AWS_SECRET_KEY"),
        upload_bucket_name=os.getenv("AWS_BUCKET_NAME"),
    )


class S3Client(BaseStorageClient):
    """
    S3Client to interact with AWS S3
    """

    @retry(
        reraise=True,
        stop=stop_after_attempt(4),
        wait=wait_fixed(4),
        after=after_log(logger, logging.DEBUG),
        before_sleep=before_sleep_log(logger, logging.DEBUG),
    )
    def __init__(
        self,
        region_name: str,
        aws_access_key_id: str,
        aws_secret_access_key: str,
        upload_bucket_name: str,
        **kwargs,
    ):
        """
        Initialize S3 client

        Args:
            region_name (str): AWS region name
            aws_access_key_id (str): AWS access key
            aws_secret_access_key (str): AWS secret key
            upload_bucket_name (str): Bucket name to upload files
        """
        self.upload_bucket_name = upload_bucket_name
        self.client = boto3.client(
            service_name="s3",
            region_name=region_name,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
        )

        self.test_connection()
        logger.info("S3Client initialized successfully !!!")

    def get_upload_bucket_name(self) -> str:
        return self.upload_bucket_name

    @classmethod
    def get_instance(
        cls,
        region_name: str,
        aws_access_key_id: str,
        aws_secret_access_key: str,
        upload_bucket_name: str,
    ):
        """
        Get S3Client instance

        Args:
            region_name (str): AWS region name
            aws_access_key_id (str): AWS access key
            aws_secret_access_key (str): AWS secret key
            upload_bucket_name (str): Bucket name to upload files

        Returns:
            S3Client: S3Client instance
        """
        return cls(
            region_name=region_name,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            upload_bucket_name=upload_bucket_name,
        )

    def test_connection(self):
        """
        Test the connection with the S3Client by listing buckets
        """
        try:
            self.client.list_objects_v2(Bucket=self.upload_bucket_name)
        except Exception as e:
            logger.error(e)
            raise ConnectionError("S3 connection failed")

    def create_bucket(self, bucket_name: str, region: str | None = None) -> None:
        """
        Create bucket in S3

        Args:
            bucket_name (str): Bucket name
            region (str | None): Region name to create bucket in
        """
        try:
            if region is None:
                self.client.create_bucket(Bucket=bucket_name)
            else:
                location = {"LocationConstraint": region}
                self.client.create_bucket(
                    Bucket=bucket_name, CreateBucketConfiguration=location
                )
        except ClientError as e:
            logger.error(e)
            return False
        return True

    @retry(stop=stop_after_attempt(3))
    def upload_file(
        self, bucket_name: str, object_name: str, file_path: str | Path
    ) -> None:
        """
        Upload file to S3Client

        Args:
            bucket_name (str): Bucket name
            object_name (str): Object name to save in Minio
            file_path (str | Path): Local file path to be uploaded
        """
        file_path = str(file_path)

        try:
            self.client.upload_file(file_path, bucket_name, object_name)
            logger.info(f"Uploaded: {file_path} --> {bucket_name}/{object_name}")

        except ClientError as e:
            logging.error(e)
            return False
        return True

    def check_bucket_exists(self, bucket_name: str) -> bool:
        """
        Check if bucket exists in Minio

        Args:
            bucket_name (str): Bucket name

        Returns:
            bool: True if bucket exists, False otherwise
        """
        try:
            self.client.head_bucket(Bucket=bucket_name)
        except ClientError as e:
            logging.error(e)
            return False
        return True

    def download_file(self, bucket_name: str, object_name: str, file_path: str):
        """
        Download file from S3

        Args:
            bucket_name (str): Bucket name
            object_name (str): Object name to download
            file_path (str): File path to save
        """
        try:
            self.client.download_file(bucket_name, object_name, file_path)
            logger.info(f"Downloaded: {bucket_name}/{object_name} --> {file_path}")

        except ClientError as e:
            logging.error(e)
            return False
        return True

    def remove_file(self, bucket_name: str, object_name: str) -> None:
        """
        Remove file from S3

        Args:
            bucket_name (str): Bucket name
            object_name (str): Object name to remove
        """

        try:
            self.client.delete_object(Bucket=bucket_name, Key=object_name)
            logger.debug(f"Removed from S3: {bucket_name}/{object_name}")

        except ClientError as e:
            logging.error(e)
            return False

        return True
