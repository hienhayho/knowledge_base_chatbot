import sys
from pathlib import Path
from minio import Minio

sys.path.append(str(Path(__file__).parent.parent.parent))
from src.utils import get_formatted_logger
from src.settings import GlobalSettings

logger = get_formatted_logger(__file__)


def get_minio_client(setting: GlobalSettings) -> "MinioClient":
    return MinioClient(
        url=setting.minio_config.url,
        access_key=setting.minio_config.access_key,
        secret_key=setting.minio_config.secret_key,
        secure=setting.minio_config.secure,
    )


class MinioClient:
    """
    Minio client to interact with Minio server
    """

    def __init__(
        self, url: str, access_key: str, secret_key: str, secure: bool = False
    ):
        """
        Initialize Minio client

        Args:
            url (str): Minio url
            access_key (str): Minio access key
            secret_key (str): Minio secret key
            secure (bool): Enable secure connection
        """
        self.client = Minio(
            endpoint=url, access_key=access_key, secret_key=secret_key, secure=secure
        )
        logger.info("Minio client initialized successfully !!!")

    def check_bucket_exists(self, bucket_name) -> bool:
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

    def upload_file(self, bucket_name: str, object_name: str, file_path: str) -> None:
        """
        Upload file to Minio

        Args:
            bucket_name (str): Bucket name
            object_name (str): Object name to save in Minio
            file_path (str): Local file path to be uploaded
        """
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
        logger.info(f"Removed: {bucket_name}/{object_name}")

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
