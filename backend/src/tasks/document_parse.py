import time
import sys
import celery
from pathlib import Path


sys.path.append(str(Path(__file__).parent.parent.parent))

from src.readers import parse_multiple_files
from src.celery import celery_app


@celery_app.task(bind=True)
def parse_document(self: celery.Task, file: str):
    """
    Parse a document.

    Args:
        file (str | Path): The path to the document to parse.

    Returns:
        dict: The parsed document.
    """
    document = parse_multiple_files(file)

    self.update_state(state="PROGRESS", meta={"status": "Parsing document"})

    i = 0
    while i < 10:
        time.sleep(1)
        self.update_state(state="PROGRESS", meta={"status": f"Processing {i}"})
        i += 1

    return {
        "task_id": self.request.id,
        "status": "SUCCESS",
    }
