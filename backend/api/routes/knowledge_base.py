from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from src.tasks.document_parser_tasks import process_document
from celery.result import AsyncResult
from fastapi import Depends
import os
import logging
from src.dependencies import get_db_manager
from src.database.manager import DatabaseManager
from src.database.models import DocumentStatus
from api.models.knowledge_base import KnowledgeBaseCreate, KnowledgeBaseResponse, KnowledgeBaseUpdate
from api.services.knowledge_base import KnowledgeBaseService
from typing import List
from src.constants import GlobalConfig

kb_router = APIRouter()
UPLOAD_DIR = "uploads"

# --- API Endpoints ---
def get_current_user_id(db_manager: DatabaseManager = Depends(get_db_manager)):
    return db_manager.get_current_user_id()

def get_knowledge_base_id(
    knowledge_base_id: int,
    current_user_id: int = Depends(get_current_user_id),
    db_manager: DatabaseManager = Depends(get_db_manager)
):
    kb = db_manager.get_knowledge_base(knowledge_base_id, current_user_id)
    return kb.id


@kb_router.post("/upload_document")
async def upload_document(
    file: UploadFile = File(...),
    knowledge_base_id: int = Depends(get_knowledge_base_id),
    db_manager: DatabaseManager = Depends(get_db_manager)
):
    # Define allowed file extensions
    ALLOWED_EXTENSIONS = GlobalConfig.ALLOWED_EXTENSIONS

    try:
        # Check if the file extension is allowed
        file_extension = os.path.splitext(file.filename)[1].lower()
        if file_extension not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400, 
                detail=f"File type not allowed. Allowed types are: {', '.join(ALLOWED_EXTENSIONS)}"
            )

        # Check if a file with the same name already exists in the database
        existing_document = db_manager.get_document_by_name(knowledge_base_id, file.filename)
        if existing_document:
            raise HTTPException(status_code=400, detail="A file with this name already exists in the knowledge base")

        # Create a unique filename
        unique_filename = file.filename
        
        # Save the file
        file_path = os.path.join(UPLOAD_DIR, unique_filename)
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Add document to database
        document_id, document_type, documented_created = db_manager.add_document(
            knowledge_base_id=knowledge_base_id,
            file_name=unique_filename,
            file_type=file_extension,
            file_path=file_path,
            status=DocumentStatus.UPLOADED
        )
        
        # Process the document asynchronously
        # task = process_document.delay(file_path, document_id)
        
        return JSONResponse(
            content={
                "message": "File uploaded successfully",
                "file_name": unique_filename,
                "file_path": file_path,
                "document_id": document_id,
                "created_at": documented_created.isoformat(),
                "file_type": document_type
                # "task_id": task.id
            },
            status_code=202
        )
    except HTTPException as he:
        raise he
    except Exception as e:
        logging.error(e)
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
        

@kb_router.get("/document_status/{document_id}")
async def get_document_status(
    document_id: int,
    db_manager: DatabaseManager = Depends(get_db_manager)
):
    document = db_manager.get_document(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    response = {
        "document_id": document_id,
        "status": document.status.value,
        "file_name": document.file_name,
        "created_at": document.created_at.isoformat(),
        "updated_at": document.updated_at.isoformat()
    }

    if document.status == DocumentStatus.PROCESSING:
        # Check Celery task status
        task_id = db_manager.get_document_task_id(document_id)
        if task_id:
            task_result = AsyncResult(task_id)
            if task_result.state == 'PROGRESS':
                response["progress"] = task_result.info
            elif task_result.ready():
                if task_result.successful():
                    response["status"] = DocumentStatus.PROCESSED.value
                    db_manager.update_document_status(document_id, DocumentStatus.PROCESSED)
                else:
                    response["status"] = DocumentStatus.FAILED.value
                    response["error"] = str(task_result.result)
                    db_manager.update_document_status(document_id, DocumentStatus.FAILED)

    return JSONResponse(content=response)


@kb_router.post("/process_document/{document_id}")
async def process_uploaded_document(
    document_id: int,
    db_manager: DatabaseManager = Depends(get_db_manager)
):
    document = db_manager.get_document(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    if document.status != DocumentStatus.UPLOADED:
        raise HTTPException(status_code=400, detail="Document is not in 'uploaded' status")
    
    db_manager.update_document_status(document_id, DocumentStatus.PROCESSING)
    
    # Start processing...
    task = process_document.delay(document.file_path, document_id)
    
    # Store the task_id
    db_manager.set_document_task_id(document_id, task.id)
    
    return JSONResponse(
        content={
            "message": "Document processing started",
            "document_id": document_id,
            "task_id": task.id
        },
        status_code=202
    )
    
@kb_router.get("/download_document/{document_id}")
async def download_document(
    document_id: int,
    db_manager: DatabaseManager = Depends(get_db_manager)
):
    document = db_manager.get_document(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    file_path = document.file_path
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(file_path, filename=document.file_name, media_type='application/octet-stream')

@kb_router.delete("/delete_document/{document_id}")
async def delete_document(
    document_id: int,
    db_manager: DatabaseManager = Depends(get_db_manager)
):
    document = db_manager.get_document(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Delete the file from the filesystem
    if os.path.exists(document.file_path):
        os.remove(document.file_path)
    
    # Delete the document from the database
    db_manager.delete_document(document_id)
    
    return JSONResponse(content={"message": "Document deleted successfully"}, status_code=200)

# ... (rest of the existing code remains the same)


@kb_router.post("/", response_model=KnowledgeBaseResponse)
async def create_knowledge_base(
    kb: KnowledgeBaseCreate,
    current_user_id: int = Depends(get_current_user_id),
    kb_service: KnowledgeBaseService = Depends()
):
    return kb_service.create_knowledge_base(current_user_id, kb)

@kb_router.get("/{kb_id}", response_model=KnowledgeBaseResponse)
async def read_knowledge_base(
    kb_id: int,
    current_user_id: int = Depends(get_current_user_id),
    kb_service: KnowledgeBaseService = Depends()
):
    kb = kb_service.get_knowledge_base(kb_id, current_user_id)
    if kb is None:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    return kb

@kb_router.get("/", response_model=List[KnowledgeBaseResponse])
async def list_knowledge_bases(
    current_user_id: int = Depends(get_current_user_id),
    kb_service: KnowledgeBaseService = Depends()
):
    return kb_service.list_knowledge_bases(current_user_id)

@kb_router.put("/{kb_id}", response_model=KnowledgeBaseResponse)
async def update_knowledge_base(
    kb_id: int,
    kb_update: KnowledgeBaseUpdate,
    current_user_id: int = Depends(get_current_user_id),
    kb_service: KnowledgeBaseService = Depends()
):
    updated_kb = kb_service.update_knowledge_base(kb_id, current_user_id, kb_update)
    if updated_kb is None:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    return updated_kb

@kb_router.delete("/{kb_id}", response_model=dict)
async def delete_knowledge_base(
    kb_id: int,
    current_user_id: int = Depends(get_current_user_id),
    kb_service: KnowledgeBaseService = Depends()
):
    success = kb_service.delete_knowledge_base(kb_id, current_user_id)
    if not success:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    return {"message": "Knowledge base deleted successfully"}