import sys
import celery
from pathlib import Path
from sqlmodel import Session


sys.path.append(str(Path(__file__).parent.parent.parent))

from src.celery import celery_app
from src.database import DatabaseManager
from src.readers import parse_multiple_files


@celery_app.task(bind=True)
def parse_document(
    self: celery.Task, file: str, db_session: Session, db_manager: DatabaseManager
):
    """
    Parse a document.

    Args:
        file (str | Path): The path to the document to parse.

    Returns:
        dict: The parsed document.
    """
    document = parse_multiple_files(file)

    self.update_state(state="PROGRESS", meta={"progress": 0})

    chunks = db_manager.get_contextual_rag_chunks(document)  # noqa

    return {
        "task_id": self.request.id,
        "status": "SUCCESS",
    }
