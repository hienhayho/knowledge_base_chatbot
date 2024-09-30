import os
import magic
import asyncio
from abc import ABC, abstractmethod
from typing import Dict, List, Type, Union
from src.celery import celery
from datetime import datetime
from llama_index.core.text_splitter import SentenceSplitter
from llama_index.core.schema import Document
import logging
import src.document_parser.readers as readers
from src.document_parser.embedding import get_embedding
from src.database.manager import DatabaseManager
from src.database.models import DocumentStatus
from src.dependencies import get_database_manager
from src.constants import GlobalConfig


class FileProcessor(ABC):
    @abstractmethod
    def process(self, file_path: str) -> Dict:
        pass


class TextFileProcessor(FileProcessor):
    def __init__(self, reader_class):
        self.reader_class = reader_class

    def process(self, file_path: str) -> Dict:
        reader = self.reader_class(return_full_document=True)
        docs: List[Document] = reader.load_data(file_path)

        splitter = SentenceSplitter()
        chunks = splitter.split_text("\n".join([doc.text for doc in docs]))
        chunks = [Document(text=chunk, metadata=docs[0].metadata) for chunk in chunks]

        return {
            "file_type": self.reader_class.__name__.replace("Reader", ""),
            "file_path": file_path,
            "processed_at": datetime.now().isoformat(),
            "chunks": len(chunks),
            "documents": chunks,
        }


class VideoFileProcessor(FileProcessor):
    def __init__(self, reader_class):
        self.reader_class = reader_class

    async def async_process(self, file_path: str) -> Dict:
        reader = self.reader_class()
        docs: List[Document] = await reader.load_data(file_path)

        return {
            "file_type": "Video",
            "file_path": file_path,
            "processed_at": datetime.now().isoformat(),
            "chunks": len(docs),
            "documents": docs,
        }

    def process(self, file_path: str) -> Dict:
        return asyncio.run(self.async_process(file_path))


def create_processor_class(reader_class):
    if reader_class.__name__ == "VideoReader":
        return VideoFileProcessor(reader_class)
    else:

        class DynamicProcessor(TextFileProcessor):
            def __init__(self):
                super().__init__(reader_class)

        return DynamicProcessor()


class FileProcessorFactory:
    _processors: Dict[str, Type[FileProcessor]] = {}
    _file_extensions: Dict[str, str] = {
        ".docx": "Docx",
        ".hwp": "HWP",
        ".pdf": "PDF",
        ".epub": "Epub",
        ".txt": "Flat",
        ".html": "HTMLTag",
        ".htm": "HTMLTag",
        ".ipynb": "IPYNB",
        ".md": "Markdown",
        ".mbox": "Mbox",
        ".pptx": "Pptx",
        ".csv": "CSV",
        ".xml": "XML",
        ".rtf": "RTF",
        ".mp4": "Video",
    }

    @classmethod
    def initialize(cls):
        for ext, reader_name in cls._file_extensions.items():
            reader_class = getattr(readers, f"{reader_name}Reader", None)
            if reader_class:
                processor_class = create_processor_class(reader_class)
                cls._processors[ext] = processor_class

    @classmethod
    def get_processor(cls, file_path: str) -> Union[FileProcessor, VideoFileProcessor]:
        if not cls._processors:
            cls.initialize()

        file_extension = os.path.splitext(file_path)[1].lower()

        if file_extension in cls._processors:
            return cls._processors[file_extension]

        # If extension is not recognized, use MIME type detection
        mime_type = cls.detect_mime_type(file_path)
        file_type = cls.mime_to_file_type(mime_type)

        processor_class = cls._processors.get(
            file_type, create_processor_class(readers.FlatReader)
        )
        return processor_class()

    @classmethod
    def register_processor(cls, file_extension: str, reader_class):
        processor_class = create_processor_class(reader_class)
        cls._processors[file_extension] = processor_class

    @staticmethod
    def detect_mime_type(file_path: str) -> str:
        mime = magic.Magic(mime=True)
        return mime.from_file(file_path)

    @staticmethod
    def mime_to_file_type(mime_type: str) -> str:
        mime_to_type = {
            "application/pdf": ".pdf",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
            "application/vnd.openxmlformats-officedocument.presentationml.presentation": ".pptx",
            "application/vnd.ms-powerpoint": ".ppt",
            "application/epub+zip": ".epub",
            "text/plain": ".txt",
            "text/html": ".html",
            "image/jpeg": ".jpg",
            "image/png": ".png",
            "application/x-ipynb+json": ".ipynb",
            "text/markdown": ".md",
            "application/mbox": ".mbox",
            "text/csv": ".csv",
            "video/mp4": ".mp4",
            "audio/mpeg": ".mp3",
            "application/xml": ".xml",
            "text/rtf": ".rtf",
            # Add more mappings as needed
        }
        return mime_to_type.get(mime_type, ".txt")  # Default to .txt for unstructured


@celery.task(bind=True)
def process_document(
    self,
    file_path: str,
    document_id: int,
    db_manager: DatabaseManager = get_database_manager(),
):
    try:
        db_manager.update_document_status(document_id, DocumentStatus.PROCESSING)
        logging.info(f"Processing document {document_id} at {file_path}")
        processor = FileProcessorFactory.get_processor(file_path)
        result = processor.process(file_path)

        chunks: List[Document] = result.get("documents", [])
        total_chunks = len(chunks)

        for i, chunk in enumerate(chunks):
            logging.info(f"Processing chunk {i+1} of {total_chunks}")
            db_manager.add_document_chunk(
                document_id=document_id,
                chunk_index=i,
                content=chunk.text,
                vector=get_embedding(chunk.text),
                metadata=chunk.metadata,
            )

            self.update_state(
                state="PROGRESS", meta={"current": i + 1, "total": total_chunks}
            )

        db_manager.update_document_status(document_id, DocumentStatus.PROCESSED)

        return {
            "status": "success",
            "message": "Document processed successfully",
            "total_chunks": total_chunks,
        }
    except Exception as e:
        db_manager.update_document_status(document_id, DocumentStatus.FAILED)
        raise e
