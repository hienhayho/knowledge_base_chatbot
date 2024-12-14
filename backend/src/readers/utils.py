# This file contains utility functions for the readers module.

import sys
from pathlib import Path
from dotenv import load_dotenv

sys.path.append(str(Path(__file__).parent.parent.parent))

from llama_index.readers.json import JSONReader
from llama_index.readers.file import (
    PptxReader,  # noqa
    PandasExcelReader,
    UnstructuredReader,
    MarkdownReader,
    IPYNBReader,
    MboxReader,
    XMLReader,
    PDFReader,
    RTFReader,
)

from .kotaemon import (
    DocxReader,
    TxtReader,
    PandasCSVReaderCustomised,
)  # noqa
from src.constants import SUPPORTED_FILE_EXTENSIONS
from src.utils import get_formatted_logger
from src.settings import GlobalSettings

setting = GlobalSettings()

load_dotenv()
logger = get_formatted_logger(__file__)


def check_valid_extenstion(file_path: str | Path) -> bool:
    """
    Check if the file extension is supported

    Args:
        file_path (str | Path): File path to check

    Returns:
        bool: True if the file extension is supported, False otherwise.
    """
    return Path(file_path).suffix in SUPPORTED_FILE_EXTENSIONS


def get_files_from_folder_or_file_paths(files_or_folders: list[str]) -> list[str]:
    """
    Get all files from the list of file paths or folders

    Args:
        files_or_folders (list[str]): List of file paths or folders

    Returns:
        list[str]: List of valid file paths.
    """
    files = []

    for file_or_folder in files_or_folders:
        if Path(file_or_folder).is_dir():
            files.extend(
                [
                    str(file_path.resolve())
                    for file_path in Path(file_or_folder).rglob("*")
                    if check_valid_extenstion(file_path)
                ]
            )

        else:
            if check_valid_extenstion(file_or_folder):
                files.append(str(Path(file_or_folder).resolve()))
            else:
                logger.warning(f"Invalid file: {file_or_folder}")

    return files


def get_extractor():
    return {
        # ".pdf": LlamaParse(
        #     result_type="markdown",
        #     api_key=setting.api_keys.LLAMA_PARSE_API_KEY,
        # ),
        ".pdf": PDFReader(),
        ".docx": DocxReader(),
        ".html": UnstructuredReader(),
        # ".csv": PandasCSVReader(pandas_config=dict(on_bad_lines="skip")),
        ".csv": PandasCSVReaderCustomised(
            pandas_config=dict(on_bad_lines="skip"), concat_rows=True, top_k=100
        ),
        ".xlsx": PandasExcelReader(),
        ".json": JSONReader(),
        ".txt": TxtReader(),
        # ".pptx": PptxReader(),
        ".md": MarkdownReader(),
        ".ipynb": IPYNBReader(),
        ".mbox": MboxReader(),
        ".xml": XMLReader(),
        ".rtf": RTFReader(),
    }
