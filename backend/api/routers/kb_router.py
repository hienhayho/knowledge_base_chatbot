import uuid
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
from src.settings import default_settings
from api.models import (
    KnowledgeBaseRequest,
    KnowledgeBaseResponse,
    UploadFileResponse,
    GetDocumentStatusReponse,
    GetKnowledgeBase,
    GetKnowledgeBaseResponse,
    MergeKnowledgeBasesRequest,
    DeleteDocumentRequestBody,
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


UPLOAD_FOLDER = Path(default_settings.upload_temp_folder)
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

    with db_session as session:
        kb = KnowledgeBases(
            name=kb_info.name,
            description=kb_info.description,
            user=session.merge(current_user),
            is_contextual_rag=True,
        )

        session.add(kb)
        session.commit()
        session.refresh(kb)

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
    minio_client: Annotated[MinioClient, Depends(get_minio_client)],
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

        document = Documents(
            file_name=file.filename,
            file_path_in_minio=f"{uuid.uuid4()}_{file.filename}",
            file_type=Path(file.filename).suffix,
            status=FileStatus.UPLOADED,
            knowledge_base=kb,
        )

        session.add(document)
        session.commit()
        session.refresh(document)

        knowledge_base = document.knowledge_base

        minio_client.upload_file(
            bucket_name=default_settings.upload_bucket_name,
            object_name=document.file_path_in_minio,
            file_path=str(file_path),
        )

        # Remove the file in local after uploading to Minio
        Path(file_path).unlink()

        return UploadFileResponse(
            doc_id=document.id,
            file_name=document.file_name,
            file_type=document.file_type,
            status=document.status,
            knowledge_base=knowledge_base,
            created_at=document.created_at,
        )


@kb_router.post("/process/{document_id}")
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
                status_code=status.HTTP_404_NOT_FOUND, detail="Document not found !"
            )

        if document.knowledge_base.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not allowed to process this document",
            )

        is_contextual_rag = document.knowledge_base.is_contextual_rag

        isContextualRAG = is_contextual_rag

        task = parse_document.delay(
            document.file_path_in_minio,
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


@kb_router.post("/stop_processing/{document_id}")
async def stop_processing_document(
    document_id: str,
    db_session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[Users, Depends(get_current_user)],
):
    """
    Stop processing document
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
                detail="You are not allowed to stop processing this document",
            )

        task_id = document.task_id

        if not task_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Task ID not found !"
            )

        task = AsyncResult(task_id, app=celery_app)

        if task.state == "PROGRESS":
            task.revoke(terminate=True, signal="SIGKILL")

            document.status = FileStatus.FAILED

            session.add(document)
            session.commit()

            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={"message": "Processing stopped successfully"},
            )

        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"message": "Task is not in progress"},
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
            response["progress"] = task.info["progress"]

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

        session.close()

        return result


@kb_router.get("/get_kb/{kb_id}", response_model=GetKnowledgeBaseResponse)
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

        session.close()

        return kb


@kb_router.get("/download/{document_id}")
async def download_document(
    document_id: str,
    db_session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[Users, Depends(get_current_user)],
    minIoClient: Annotated[MinioClient, Depends(get_minio_client)],
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

        file_path = DOWNLOAD_FOLDER / (f"{uuid.uuid4()}_" + document.file_name)

        minIoClient.download_file(
            bucket_name=default_settings.upload_bucket_name,
            object_name=document.file_path_in_minio,
            file_path=str(file_path),
        )

        session.close()

        return FileResponse(path=file_path, filename=document.file_name)


@kb_router.patch("/merge", response_model=GetKnowledgeBase)
async def merge_knowledge_bases(
    merge_request: Annotated[MergeKnowledgeBasesRequest, Body(...)],
    db_session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[Users, Depends(get_current_user)],
    db_manager: Annotated[DatabaseManager, Depends(get_db_manager)],
):
    """
    Merge knowledge bases
    """

    with db_session as session:
        query = select(KnowledgeBases).where(
            KnowledgeBases.id.in_(merge_request.knowledge_base_ids)
        )

        knowledge_bases = session.exec(query).all()

        if not knowledge_bases:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Knowledge Bases not found !",
            )

        if any(kb.user_id != current_user.id for kb in knowledge_bases):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not allowed to merge these Knowledge Bases",
            )

        target_knowledge_base = knowledge_bases[0]
        target_knowledge_base_id = target_knowledge_base.id

        source_knowledge_bases = knowledge_bases[1:]
        source_knowledge_base_ids = [kb.id for kb in source_knowledge_bases]

        # Add all the documents from source knowledge bases to target knowledge base
        logger.debug(
            "Moving documents from source knowledge bases to target knowledge base in SQL database ..."
        )
        for kb in source_knowledge_bases:
            source_docs = kb.documents
            for doc in source_docs:
                doc.knowledge_base_id = target_knowledge_base_id
                session.add(doc)
                session.commit()

                session.refresh(doc)
                session.refresh(target_knowledge_base)
                session.refresh(kb)

        db_manager.merge_knowledge_bases(
            target_knowledge_base_id=target_knowledge_base_id,
            source_knowledge_base_ids=source_knowledge_base_ids,
        )

        target_knowledge_base.name = merge_request.name
        target_knowledge_base.description = merge_request.description

        session.add(target_knowledge_base)
        session.commit()
        session.refresh(target_knowledge_base)

        for kb in source_knowledge_bases:
            session.delete(kb)
            session.commit()

        session.close()

        return target_knowledge_base


@kb_router.delete("/delete_document/{document_id}")
async def delete_document(
    document_id: str,
    delete_document_request_body: DeleteDocumentRequestBody,
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
            delete_to_retry=delete_document_request_body.delete_to_retry,
            document_id=document.id,
            knownledge_base_id=document.knowledge_base_id,
            is_contextual_rag=is_contextual_rag,
        )

        if not delete_document_request_body.delete_to_retry:
            session.delete(document)
            session.commit()

        session.close()

        return JSONResponse(
            content={"message": "Document deleted successfully"},
            status_code=status.HTTP_200_OK,
        )


@kb_router.delete("/delete_kb/{knowledge_base_id}")
async def delete_knowledge_base(
    knowledge_base_id: str,
    db_session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[Users, Depends(get_current_user)],
    db_manager: Annotated[DatabaseManager, Depends(get_db_manager)],
):
    """
    Delete knowledge base
    """
    with db_session as session:
        query = select(KnowledgeBases).where(KnowledgeBases.id == knowledge_base_id)

        kb = session.exec(query).first()

        if not kb:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Knowledge Base not found !",
            )

        if kb.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not allowed to delete this Knowledge Base",
            )

        for doc in kb.documents:
            db_manager.delete_file(
                object_name=doc.file_path_in_minio,
                document_id=doc.id,
                knownledge_base_id=kb.id,
                is_contextual_rag=kb.is_contextual_rag,
            )

        session.delete(kb)
        session.commit()
        session.close()

        return JSONResponse(
            content={"message": "Knowledge Base deleted successfully"},
            status_code=status.HTTP_200_OK,
        )
