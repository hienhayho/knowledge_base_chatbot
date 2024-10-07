from pathlib import Path
from typing import Annotated
from sqlmodel import Session, select
from sqlalchemy.orm import joinedload
from celery.result import AsyncResult
from fastapi.responses import JSONResponse, FileResponse
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
from src.settings import GlobalSettings, get_default_setting
from api.models import (
    KnowledgeBaseRequest,
    KnowledgeBaseResponse,
    UploadFileResponse,
    GetDocumentStatusReponse,
    GetKnowledgeBase,
    GetKnowledgeBaseResponse,
)
from src.database import (
    Users,
    get_session,
    MinioClient,
    KnowledgeBases,
    DatabaseManager,
    Documents,
    get_db_manager,
    get_minio_client,
    is_valid_uuid,
)
from src.celery import celery_app
from src.tasks import parse_document
from src.utils import get_formatted_logger
from src.constants import FileStatus, ErrorResponse

logger = get_formatted_logger(__file__)

kb_router = APIRouter()

setting = GlobalSettings()

use_contextual_rag = setting.use_contextual_rag
if not use_contextual_rag:
    logger.critical(
        "ContextualRAG is disabled in the settings. So all the knowledge bases will be original RAG"
    )

UPLOAD_FOLDER = Path(setting.upload_temp_folder)
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)

DOWNLOAD_FOLDER = Path("downloads")
DOWNLOAD_FOLDER.mkdir(parents=True, exist_ok=True)


@kb_router.post("/create", response_model=KnowledgeBaseResponse)
async def create_new_knowledge_base(
    kb_info: Annotated[KnowledgeBaseRequest, Body(...)],
    db_session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[Users, Depends(get_current_user)],
):
    """
    Create new knowledge base
    """

    # Check if the system is using ContextualRAG or not
    # If not, then all the knowledge bases will be original RAG
    if not use_contextual_rag:
        kb_info.is_contextual_rag = False

    with db_session as session:
        kb = KnowledgeBases(
            name=kb_info.name,
            description=kb_info.description,
            user=current_user,
            is_contextual_rag=kb_info.is_contextual_rag,
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
    db_manager: Annotated[DatabaseManager, Depends(get_db_manager)],
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
            doc_id=document.id,
            file_name=document.file_name,
            file_type=document.file_type,
            status=document.status,
            knowledge_base=knowledge_base,
        )


@kb_router.post("/process/{document_id}")
async def process_document(
    document_id: str,
    db_session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[Users, Depends(get_current_user)],
    db_manager: Annotated[DatabaseManager, Depends(get_db_manager)],
):
    """
    Process document
    """
    with db_session as session:
        query = select(Documents).where(Documents.id == document_id)

        document = session.exec(query).first()

        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Document not found !"
            )

        if document.knowledge_base.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not allowed to process this document",
            )

        is_contextual_rag = document.knowledge_base.is_contextual_rag

        temp_file_path = DOWNLOAD_FOLDER / document.file_name

        db_manager.download_file(
            object_name=document.file_path_in_minio, file_path=str(temp_file_path)
        )

        isContextualRAG = is_contextual_rag

        task = parse_document.delay(
            str(temp_file_path),
            document.id,
            document.knowledge_base_id,
            isContextualRAG,
        )

        document.task_id = task.id
        document.status = FileStatus.PROCESSING

        session.add(document)
        session.commit()

        return JSONResponse(
            status_code=status.HTTP_202_ACCEPTED,
            content={"task_id": task.id, "status": "Processing"},
        )


@kb_router.get("/document_status/{document_id}")
async def get_document_status(
    document_id: str,
    db_session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[Users, Depends(get_current_user)],
):
    with db_session as session:
        query = select(Documents).where(Documents.id == document_id)

        document = session.exec(query).first()

        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Document not found !"
            )

        if document.knowledge_base.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not allowed to access this document",
            )

        task_id = document.task_id

        if document.status != FileStatus.PROCESSING:
            return GetDocumentStatusReponse(
                doc_id=document.id, status=document.status, task_id=task_id, metadata={}
            )

        if not task_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Task ID not found !"
            )

        task = AsyncResult(task_id, app=celery_app)

        state = task.state

        response = {
            "document_id": document.id,
            "file_name": document.file_name,
            "created_at": document.created_at.isoformat(),
            "updated_at": document.updated_at.isoformat(),
        }

        if state == "SUCCESS":
            response["status"] = FileStatus.PROCESSED
            response["metadata"] = {}
            document.status = FileStatus.PROCESSED

        elif state == "FAILURE":
            response["status"] = FileStatus.FAILED
            response["metadata"] = {}
            document.status = FileStatus.FAILED

        elif state == "PROGRESS":
            response["status"] = FileStatus.PROCESSING
            response["metadata"] = task.info

        session.add(document)
        session.commit()

        return response


@kb_router.get("/get_all", response_model=list[GetKnowledgeBase])
async def get_all_knowledge_bases(
    db_session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[Users, Depends(get_current_user)],
):
    """
    Get all knowledge bases
    """
    with db_session as session:
        query = select(KnowledgeBases).where(KnowledgeBases.user_id == current_user.id)

        knowledge_bases = session.exec(query).all()

        result = [
            GetKnowledgeBase(
                id=kb.id,
                name=kb.name,
                description=kb.description,
                document_count=len(kb.documents),
                last_updated=kb.last_updated,
            )
            for kb in knowledge_bases
        ]

        return result


@kb_router.get("/{kb_id}", response_model=GetKnowledgeBaseResponse)
async def get_knowledge_base(
    kb_id: str,
    db_session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[Users, Depends(get_current_user)],
):
    """
    Get knowledge base by ID
    """
    with db_session as session:
        query = (
            select(KnowledgeBases)
            .options(joinedload(KnowledgeBases.documents))
            .filter_by(id=kb_id, user_id=current_user.id)
        )

        kb = session.exec(query).first()

        if not kb:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Knowledge Base not found !",
            )

        if kb.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not allowed to access this Knowledge Base",
            )

        return GetKnowledgeBaseResponse.model_validate(kb)


@kb_router.get("/download/{document_id}")
async def download_document(
    document_id: str,
    db_session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[Users, Depends(get_current_user)],
    minIoClient: Annotated[MinioClient, Depends(get_minio_client)],
    setting: Annotated[GlobalSettings, Depends(get_default_setting)],
):
    """
    Download document
    """
    with db_session as session:
        query = select(Documents).where(Documents.id == document_id)

        document = session.exec(query).first()

        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Document not found !"
            )

        if document.knowledge_base.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not allowed to download this document",
            )

        file_path = DOWNLOAD_FOLDER / document.file_name

        minIoClient.download_file(
            bucket_name=setting.upload_bucket_name,
            object_name=document.file_path_in_minio,
            file_path=str(file_path),
        )

        return FileResponse(path=file_path, filename=document.file_name)


@kb_router.delete("/delete/{document_id}")
async def delete_document(
    document_id: str,
    db_session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[Users, Depends(get_current_user)],
    db_manager: Annotated[DatabaseManager, Depends(get_db_manager)],
):
    """
    Delete document
    """
    with db_session as session:
        query = select(Documents).where(Documents.id == document_id)

        document = session.exec(query).first()

        is_contextual_rag = document.knowledge_base.is_contextual_rag

        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Document not found !"
            )

        if document.knowledge_base.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not allowed to delete this document",
            )

        db_manager.delete_file(
            object_name=document.file_path_in_minio,
            document_id=document.id,
            knownledge_base_id=document.knowledge_base_id,
            is_contextual_rag=is_contextual_rag,
        )

        session.delete(document)
        session.commit()

        return JSONResponse(
            content={"message": "Document deleted successfully"},
            status_code=status.HTTP_200_OK,
        )
