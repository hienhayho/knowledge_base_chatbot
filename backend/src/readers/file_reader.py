# This file contains the core function to parse documents from multiple files.

import sys
from typing import Any
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

from dotenv import load_dotenv
from llama_index.core import Document
from llama_index.core import SimpleDirectoryReader
from .utils import get_files_from_folder_or_file_paths

from src.utils import get_formatted_logger

load_dotenv()

logger = get_formatted_logger(__file__)


def parse_multiple_files(
    files_or_folder: list[str] | str, extractor: dict[str, Any]
) -> list[Document]:
    """
    Read the content of multiple files.

    Args:
        files_or_folder (list[str] | str): List of file paths or folder paths containing files.
        extractor (dict[str, Any]): Extractor to extract content from files.
    Returns:
        list[Document]: List of documents from all files.
    """
    assert extractor, "Extractor is required."

    if isinstance(files_or_folder, str):
        files_or_folder = [files_or_folder]

    valid_files = get_files_from_folder_or_file_paths(files_or_folder)

    if len(valid_files) == 0:
        raise ValueError("No valid files found.")

    logger.info(f"Valid files: {valid_files}")

    documents = SimpleDirectoryReader(
        input_files=valid_files,
        file_extractor=extractor,
    ).load_data(show_progress=True)

    return documents
