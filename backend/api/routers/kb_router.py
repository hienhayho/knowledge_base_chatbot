import os
import copy
import uuid
from pathlib import Path
from collections import deque
from typing import Annotated
from celery.result import AsyncResult
from sqlmodel import Session, select, not_, col, or_, and_
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
    UserResponse,
    KnowledgeBaseRequest,
    KnowledgeBaseResponse,
    UploadFileResponse,
    GetDocumentStatusReponse,
    GetKnowledgeBase,
    GetKnowledgeBaseResponse,
    DeleteDocumentRequestBody,
    DocumentInKnowledgeBase,
    InheritKnowledgeBaseRequest,
    InheritableKnowledgeBaseResponse,
)
from src.database import (
    Users,
    Documents,
    Assistants,
    DocumentChunks,
    get_session,
    MinioClient,
    is_valid_uuid,
    get_db_manager,
    KnowledgeBases,
    DatabaseManager,
    get_minio_client,
)
from src.celery import celery_app
from src.tasks import parse_document
from src.utils import get_formatted_logger, is_product_file
from src.constants import FileStatus, ErrorResponse, DOWNLOAD_FOLDER

logger = get_formatted_logger(__file__)

kb_router = APIRouter()


UPLOAD_FOLDER = Path(default_settings.upload_temp_folder)
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)

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
            user_id=current_user.id,
            is_contextual_rag=True,
        )

        session.add(kb)
        session.commit()
        session.refresh(kb)

        return KnowledgeBaseResponse(
            id=kb.id,
            name=kb.name,
            description=kb.description,
            created_at=kb.created_at,
            updated_at=kb.updated_at,
            user=UserResponse(
                id=current_user.id,
                role=current_user.role,
                username=current_user.username,
                created_at=current_user.created_at,
                updated_at=current_user.updated_at,
            ),
        )


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

    with open(file_path, "rb") as f:
        f.seek(0, os.SEEK_END)
        file_size = f.tell()

    with db_session as session:
        query = select(KnowledgeBases).where(KnowledgeBases.id == knowledge_base_id)

        kb = session.exec(query).first()

        query_documents = select(Documents).where(
            Documents.user_id == current_user.id,
        )

        documents = session.exec(query_documents).all()

        if not kb:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge Base not found"
            )

        if not current_user.allow_upload(file_size, documents):
            logger.debug(
                "Deleting the file from local as user has no space left for uploading files"
            )
            Path(file_path).unlink()
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"No space left for uploading files, used: {round(current_user.total_upload_size(documents=documents), 2)} MB. Allowed space: {current_user.max_size_mb} MB. This file size: {round(file_size / (1024 * 1024), 2)} MB",
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
            is_product_file=is_product_file(file_path),
            file_size=file_size,
            knowledge_base_id=knowledge_base_id,
            user_id=current_user.id,
        )

        session.add(document)
        session.commit()
        session.refresh(document)

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
            knowledge_base=kb,
            created_at=document.created_at,
            file_size_in_mb=document.file_size_in_mb,
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

        query_kb = select(KnowledgeBases).where(
            KnowledgeBases.id == document.knowledge_base_id
        )

        kb = session.exec(query_kb).first()

        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Document not found !"
            )

        if document.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not allowed to process this document",
            )

        is_contextual_rag = kb.is_contextual_rag

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

        if document.user_id != current_user.id:
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

        if document.user_id != current_user.id:
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

        documents = [
            session.exec(
                select(Documents).where(Documents.knowledge_base_id == kb.id)
            ).all()
            for kb in knowledge_bases
        ]

        result = [
            GetKnowledgeBase(
                id=kb.id,
                name=kb.name,
                description=kb.description,
                document_count=len(document),
                last_updated=kb.last_updated,
            )
            for kb, document in zip(knowledge_bases, documents)
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
        query = select(KnowledgeBases).filter_by(id=kb_id, user_id=current_user.id)

        kb = session.exec(query).first()

        query_documents = select(Documents).where(Documents.knowledge_base_id == kb_id)

        documents = session.exec(query_documents).all()

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

        if kb.parents:
            mergeable_kb = []
        else:
            mergeable_kb = session.exec(
                select(KnowledgeBases.id, KnowledgeBases.name)
                .join(Users, KnowledgeBases.user_id == Users.id)
                .where(
                    Users.organization == current_user.organization,
                    not_(
                        or_(
                            col(KnowledgeBases.parents).contains([kb.id]),
                            col(KnowledgeBases.children).contains([kb.id]),
                        ),
                    ),
                    not_(KnowledgeBases.id == kb.id),
                    and_(kb.children == []),
                )
            ).all()

        session.close()

        return GetKnowledgeBaseResponse(
            id=kb.id,
            name=kb.name,
            description=kb.description,
            user_id=kb.user_id,
            created_at=kb.created_at,
            updated_at=kb.updated_at,
            document_count=len(documents),
            last_updated=kb.last_updated,
            parents=kb.parents,
            children=kb.children,
            documents=[
                DocumentInKnowledgeBase(
                    id=doc.id,
                    file_name=doc.file_name,
                    file_type=doc.file_type,
                    status=doc.status,
                    created_at=doc.created_at,
                    file_size_in_mb=doc.file_size_in_mb,
                )
                for doc in documents
            ],
            inheritable_knowledge_bases=(
                [
                    InheritableKnowledgeBaseResponse(id=kb.id, name=kb.name)
                    for kb in mergeable_kb
                ]
            ),
        )


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

        if document.user_id != current_user.id:
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

        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Document not found !"
            )

        if document.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not allowed to delete this document",
            )

        db_manager.delete_file(
            object_name=document.file_path_in_minio,
            delete_to_retry=delete_document_request_body.delete_to_retry,
            document_id=document.id,
        )

        document_chunks = session.exec(
            select(DocumentChunks).where(DocumentChunks.document_id == document_id)
        ).all()

        for chunk in document_chunks:
            session.delete(chunk)
            session.commit()

        if not delete_document_request_body.delete_to_retry:
            session.delete(document)
            session.commit()

        session.close()

        return JSONResponse(
            content={"message": "Document deleted successfully"},
            status_code=status.HTTP_200_OK,
        )


@kb_router.post("/inherit_kb")
async def inherit_knowledge_base(
    inherit_kb_request: InheritKnowledgeBaseRequest,
    db_session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[Users, Depends(get_current_user)],
):
    """
    Inherit knowledge base
    """
    with db_session as session:
        target_kb_id = inherit_kb_request.target_knowledge_base_id
        source_kb_id = inherit_kb_request.source_knowledge_base_id
        if not target_kb_id:
            target_kb = KnowledgeBases(
                name=f"{current_user.username}'s inherited KB",
                description="Inherited from another KB",
                user_id=current_user.id,
                is_contextual_rag=True,
            )

            session.add(target_kb)
            session.commit()
            session.refresh(target_kb)
            target_kb_id = target_kb.id

        else:
            target_kb = session.exec(
                select(KnowledgeBases).where(
                    KnowledgeBases.id == target_kb_id,
                    KnowledgeBases.user_id == current_user.id,
                )
            ).first()

            if not target_kb:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Target Knowledge Base not found !",
                )

        if len(target_kb.children) >= 1:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Target Knowledge Base is already inheriting another Knowledge Base",
            )

        source_kb = session.exec(
            select(KnowledgeBases).where(KnowledgeBases.id == source_kb_id)
        ).first()

        if not source_kb:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Source Knowledge Base not found !",
            )

        if target_kb_id in source_kb.parents:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Target Knowledge Base is already inheriting the Source Knowledge Base",
            )

        target_kb_parent = copy.deepcopy(source_kb.parents)
        target_kb_parent.append(source_kb_id)
        target_kb.parents = list(set(target_kb_parent))

        source_kb_children = copy.deepcopy(source_kb.children)
        source_kb_children.append(target_kb_id)
        source_kb.children = list(set(source_kb_children))

        session.add(target_kb)
        session.commit()
        session.add(source_kb)
        session.commit()

        session.close()

        return JSONResponse(
            content={"message": "Knowledge Base inherited successfully"},
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

        # Delete all the documents and its chunks in its old knowledge base
        documents = session.exec(
            select(Documents).where(Documents.knowledge_base_id == knowledge_base_id)
        ).all()
        for doc in documents:
            db_manager.delete_file(
                object_name=doc.file_path_in_minio,
                document_id=doc.id,
                delete_to_retry=False,
            )

            document_chunks = session.exec(
                select(DocumentChunks).where(DocumentChunks.document_id == doc.id)
            ).all()

            for chunk in document_chunks:
                session.delete(chunk)
                session.commit()

            session.delete(doc)
            session.commit()

        # Delete the assistants associated with the knowledge base
        assistants_ids = session.exec(
            select(Assistants.id).where(
                Assistants.knowledge_base_id == knowledge_base_id
            )
        ).all()

        for assistant_id in assistants_ids:
            db_manager.delete_assistant(assistant_id=assistant_id)

        parents_copy = copy.deepcopy(kb.parents)
        # Delete the knowledge base from the parents of this knowledge base. Mean that this deleted knowledge base is no longer inheriting its parents
        for parent_id in kb.parents:
            parent_kb = session.exec(
                select(KnowledgeBases).where(KnowledgeBases.id == parent_id)
            ).first()

            parent_kb_children = copy.deepcopy(parent_kb.children)
            parent_kb_children = [
                child for child in parent_kb_children if child != kb.id
            ]
            parent_kb.children = list(set(parent_kb_children))

            session.add(parent_kb)
            session.commit()

        # Delete the knowledge base from the children of its parents. Mean that the knowledge base is no longer inheriting its parents
        queue = deque(kb.children)
        parents_copy.append(kb.id)

        while queue:
            child_id = queue.popleft()
            child_kb = session.exec(
                select(KnowledgeBases).where(KnowledgeBases.id == child_id)
            ).first()

            child_kb_parents = copy.deepcopy(child_kb.parents)
            child_kb_parents = [
                parent for parent in child_kb_parents if parent not in parents_copy
            ]
            child_kb.parents = list(set(child_kb_parents))

            session.add(child_kb)
            session.commit()

            queue.extend(child_kb.children)

        # Finally, delete the knowledge base itself
        session.delete(kb)
        session.commit()
        session.close()

        return JSONResponse(
            content={"message": "Knowledge Base deleted successfully"},
            status_code=status.HTTP_200_OK,
        )
