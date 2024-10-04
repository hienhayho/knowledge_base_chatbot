import sys
import math
import celery
from pathlib import Path
from sqlmodel import Session


sys.path.append(str(Path(__file__).parent.parent.parent))

from src.celery import celery_app
from src.settings import defaul_settings
from src.readers import parse_multiple_files
from src.database import (
    DatabaseManager,
    DocumentChunks,
    get_session,
    get_db_manager,
)

db_session: Session = get_session(setting=defaul_settings)
db_manager: DatabaseManager = get_db_manager(setting=defaul_settings)


@celery_app.task(bind=True)
def parse_document(
    self: celery.Task,
    file_path: str,
    document_id: str,
    knowledge_base_id: str,
):
    """
    Parse a document.

    Args:
        file_path (str | Path): The path to the document to parse.
        document_id (str): The document ID from Documents table.
        knowledge_base_id (str): The knowledge base ID as collection name for vector database and also index name for elasticsearch.

    Returns:
        dict: The task ID and status.
    """
    self.update_state(state="PROGRESS", meta={"progress": 0})

    document = parse_multiple_files(file_path)

    self.update_state(state="PROGRESS", meta={"progress": 10})

    chunks = db_manager.get_chunks(document)

    self.update_state(state="PROGRESS", meta={"progress": 20})

    contextual_documents, contextual_documents_metadata = (
        db_manager.get_contextual_rag_chunks(
            documents=document,
            chunks=chunks,
        )
    )

    self.update_state(state="PROGRESS", meta={"progress": 40})

    db_manager.es_index_document(
        index_name=knowledge_base_id,
        documents_metadata=contextual_documents_metadata,
    )

    self.update_state(state="PROGRESS", meta={"progress": 60})

    db_manager.index_to_vector_db(
        collection_name=str(knowledge_base_id), documents=contextual_documents
    )

    self.update_state(state="PROGRESS", meta={"progress": 80})

    with db_session as session:
        for idx, chunk in enumerate(contextual_documents):
            document_chunk = DocumentChunks(
                chunk_index=idx,
                content=chunk.text,
                document_id=document_id,
                vector_id=chunk.metadata["doc_id"],
            )
            session.add(document_chunk)
            session.commit()
            session.refresh(document_chunk)

            self.update_state(
                state="PROGRESS",
                meta={
                    "progress": 80
                    + math.ceil(20 / len(contextual_documents) * (idx + 1))
                },
            )

    return {
        "task_id": self.request.id,
        "status": "SUCCESS",
    }
