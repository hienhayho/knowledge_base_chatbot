from pathlib import Path
from sqlmodel import select
from sqlmodel import Session
from typing import Annotated
from fastapi.responses import JSONResponse
from fastapi import (
    Body,
    File,
    status,
    Depends,
    APIRouter,
    UploadFile,
    HTTPException,
)

from .user_router import get_current_user
from src.settings import GlobalSettings
from api.models import KnowledgeBaseRequest, KnowledgeBaseResponse, UploadFileResponse
from src.database import (
    Users,
    get_session,
    KnowledgeBases,
    DatabaseManager,
    Documents,
    is_valid_uuid,
)
from src.tasks import parse_document
from src.utils import get_formatted_logger
from src.constants import FileStatus, ErrorResponse

logger = get_formatted_logger(__file__)

kb_router = APIRouter()

setting = GlobalSettings()

UPLOAD_FOLDER = Path(setting.upload_temp_folder)
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)

db_manager = DatabaseManager(setting=setting)


@kb_router.post("/create", response_model=KnowledgeBaseResponse)
async def create_new_knowledge_base(
    kb_info: Annotated[KnowledgeBaseRequest, Body(...)],
    db_session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[Users, Depends(get_current_user)],
):
    """
    Create new knowledge base
    """
    with db_session as session:
        kb = KnowledgeBases(
            name=kb_info.name,
            description=kb_info.description,
            user=current_user,
        )

        session.add(kb)
        session.commit()
        session.refresh(kb)

        kb.user = current_user

        return kb


@kb_router.post(
    "/upload",
    response_model=UploadFileResponse,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Knowledge Base not found",
            "content": {
                "application/json": {"example": {"detail": "Knowledge Base not found"}}
            },
        },
        400: {
            "model": ErrorResponse,
            "description": "Invalid Knowledge Base ID",
            "content": {
                "application/json": {"example": {"detail": "Invalid Knowledge Base ID"}}
            },
        },
        409: {
            "model": ErrorResponse,
            "description": "File already exists in the Knowledge Base",
            "content": {
                "application/json": {
                    "example": {"detail": "File already exists in the Knowledge Base"}
                }
            },
        },
    },
)
async def upload_file(
    knowledge_base_id: str,
    file: Annotated[UploadFile, File(...)],
    db_session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[Users, Depends(get_current_user)],
):
    """
    Upload file to knowledge base for the current user
    """

    if not is_valid_uuid(knowledge_base_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Knowledge Base ID",
        )

    file_name = file.filename
    file_path = UPLOAD_FOLDER / file_name

    with file_path.open("wb") as buffer:
        buffer.write(file.file.read())

    with db_session as session:
        query = select(KnowledgeBases).where(KnowledgeBases.id == knowledge_base_id)

        kb = session.exec(query).first()

        if not kb:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge Base not found"
            )

        if kb.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not allowed to upload to this Knowledge Base",
            )

        query = select(Documents).where(
            Documents.knowledge_base_id == knowledge_base_id,
            Documents.file_name == file.filename,
        )

        document_exist = session.exec(query).first()

        if document_exist:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="File already exists in the Knowledge Base",
            )

        document = Documents(
            file_name=file.filename,
            file_path_in_minio=f"{knowledge_base_id}/{file.filename}",
            file_type=Path(file.filename).suffix,
            status=FileStatus.UPLOADED,
            knowledge_base=kb,
        )

        session.add(document)
        session.commit()
        session.refresh(document)

        knowledge_base = document.knowledge_base

        db_manager.upload_file(
            object_name=document.file_path_in_minio, file_path=str(file_path)
        )

        # Remove the file after uploading to Minio
        Path(file_path).unlink()

        return UploadFileResponse(
            file_name=document.file_name,
            file_type=document.file_type,
            status=document.status,
            knowledge_base=knowledge_base,
        )


@kb_router.post("/process")
async def process_document(
    document_id: str,
    db_session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[Users, Depends(get_current_user)],
):
    """
    Process document
    """
    with db_session as session:
        query = select(Documents).where(Documents.id == document_id)

        document = session.exec(query).first()

        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
            )

        if document.knowledge_base.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not allowed to process this document",
            )

        temp_file_path = UPLOAD_FOLDER / document.file_name

        db_manager.download_file(
            object_name=document.file_path_in_minio, file_path=str(temp_file_path)
        )

        task = parse_document.delay(temp_file_path)

        return JSONResponse(
            status_code=status.HTTP_202_ACCEPTED,
            content={"task_id": task.id, "status": "Processing"},
        )
