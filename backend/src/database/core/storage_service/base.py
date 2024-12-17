import sys
import logging
from pathlib import Path
from abc import ABC, abstractmethod
from tenacity import retry, stop_after_attempt, wait_fixed, after_log, before_sleep_log

sys.path.append(str(Path(__file__).parent.parent.parent.parent))
from src.utils import get_formatted_logger

logger = get_formatted_logger(__file__)


class BaseStorageClient(ABC):
    """
    Base abstract class for storage clients
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
        *args,
        **kwargs,
    ):
        """
        Initialize storage client
        """
        ...

    def get_upload_bucket_name(self) -> str:
        """
        Get the upload bucket name

        Returns:
            str: Upload bucket name
        """
        ...

    @abstractmethod
    def test_connection(self):
        """
        Test the connection with the storage service server by listing buckets
        """
        ...

    @abstractmethod
    def check_bucket_exists(self, bucket_name: str) -> bool:
        """
        Check if bucket exists in storage service

        Args:
            bucket_name (str): Bucket name

        Returns:
            bool: True if bucket exists, False otherwise
        """
        ...

    @abstractmethod
    def create_bucket(self, bucket_name: str) -> None:
        """
        Create bucket in storage service

        Args:
            bucket_name (str): Bucket name
        """
        ...

    @abstractmethod
    @retry(stop=stop_after_attempt(3))
    def upload_file(
        self, bucket_name: str, object_name: str, file_path: str | Path
    ) -> None:
        """
        Upload file to storage service

        Args:
            bucket_name (str): Bucket name
            object_name (str): Object name to save in storage service
            file_path (str | Path): Local file path to be uploaded
        """
        ...

    @abstractmethod
    def download_file(self, bucket_name: str, object_name: str, file_path: str):
        """
        Download file from storage service

        Args:
            bucket_name (str): Bucket name
            object_name (str): Object name to download
            file_path (str): File path to save
        """
        ...

    @abstractmethod
    def remove_file(self, bucket_name: str, object_name: str) -> None:
        """
        Remove file from storage service

        Args:
            bucket_name (str): Bucket name
            object_name (str): Object name to remove
        """
        ...

    def remove_bucket(self, bucket_name: str) -> None:
        """
        Remove bucket from storage service

        Args:
            bucket_name (str): Bucket name
        """
        ...
