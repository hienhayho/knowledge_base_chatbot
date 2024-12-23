import sys
import math
import celery
from typing import Type
from pathlib import Path
from llama_index.core import Document
from llama_index.core.readers.base import BaseReader

sys.path.append(str(Path(__file__).parent.parent.parent))

from src.celery import celery_app
from src.settings import default_settings
from src.utils import get_formatted_logger, is_product_file
from src.readers import parse_multiple_files, get_extractor
from src.database import (
    DatabaseManager,
    DocumentChunks,
    get_instance_session,
)

logger = get_formatted_logger(__file__)

db_manager: DatabaseManager = DatabaseManager.from_setting(setting=default_settings)


class FileExtractor:
    def __init__(self) -> None:
        self.extractor = get_extractor()

    def get_extractor_for_file(
        self, file_path: str | Path
    ) -> dict[str, Type[BaseReader]]:
        """
        Get specific reader for file

        Args:
            file_path (str): file path to extract content

        Return:
            dict[str, Type[BaseReader]]: Specific reader for the file
        """
        file_suffix = Path(file_path).suffix
        return {
            file_suffix: self.extractor[file_suffix],
        }


file_extractor = FileExtractor()


@celery_app.task(bind=True)
def parse_document(
    self: celery.Task,
    file_path_in_storage_service: str,
    document_id: str,
    knowledge_base_id: str,
    is_contextual_rag: bool = True,
):
    """
    Parse a document.

    Args:
        file_path_in_storage_service (str | Path): The file path in Minio.
        document_id (str): The document ID from Documents table.
        knowledge_base_id (str): The knowledge base ID as collection name for vector database and also index name for elasticsearch.
        is_contextual_rag (bool): Whether to use contextual RAG or not (deprecated). Always set to `True`.

    Returns:
        dict: The task ID and status.
    """
    extension = Path(file_path_in_storage_service).suffix
    file_path = Path("downloads") / f"{document_id}.{extension}"

    self.update_state(state="PROGRESS", meta={"progress": 0})

    db_manager.storage_client.download_file(
        bucket_name=db_manager.storage_client.get_upload_bucket_name(),
        object_name=file_path_in_storage_service,
        file_path=file_path,
    )

    if is_product_file(file_path):
        logger.info("product file detected, skipping parsing")
        return {
            "task_id": self.request.id,
            "status": "SUCCESS",
        }

    self.update_state(state="PROGRESS", meta={"progress": 5})

    document = parse_multiple_files(
        str(file_path),
        extractor=file_extractor.get_extractor_for_file(file_path),
    )

    self.update_state(state="PROGRESS", meta={"progress": 10})

    chunks = db_manager.get_chunks(document, document_id)

    self.update_state(state="PROGRESS", meta={"progress": 20})

    if is_contextual_rag:
        contextual_documents, _ = db_manager.get_contextual_rag_chunks(
            documents=document,
            chunks=chunks,
        )

    self.update_state(state="PROGRESS", meta={"progress": 40})

    new_chunks: list[Document] = []
    for chunk in chunks:
        new_chunks.extend(chunk)

    db_manager.index_to_vector_db(
        kb_id=knowledge_base_id,
        chunks_documents=contextual_documents if is_contextual_rag else new_chunks,
        document_id=document_id,
    )

    self.update_state(state="PROGRESS", meta={"progress": 80})

    indexed_document = contextual_documents if is_contextual_rag else new_chunks

    session = get_instance_session()
    for idx, (chunk, original_chunk) in enumerate(zip(indexed_document, new_chunks)):
        document_chunk = DocumentChunks(
            chunk_index=idx,
            original_content=original_chunk.text,
            content=chunk.text,
            document_id=document_id,
            vector_id=chunk.metadata["vector_id"],
        )
        session.add(document_chunk)
        session.commit()
        session.refresh(document_chunk)

        self.update_state(
            state="PROGRESS",
            meta={"progress": 80 + math.ceil(20 / len(indexed_document) * (idx + 1))},
        )

    session.close()

    file_path.unlink()

    return {
        "task_id": self.request.id,
        "status": "SUCCESS",
    }
