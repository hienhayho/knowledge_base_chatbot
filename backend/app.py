from fastapi import FastAPI
from dotenv import load_dotenv
from api.routes.knowledge_base import kb_router
from api.routes.assistant import assistant_router
from fastapi.middleware.cors import CORSMiddleware
from celery.result import AsyncResult
from fastapi.responses import JSONResponse, FileResponse
from fastapi import FastAPI, HTTPException
import os
from pathlib import Path

BASE_DIR = Path(__file__).parent.absolute()

load_dotenv(override=True)
app = FastAPI()

@app.get("/")
async def root():
    return {
        "message": "Hello World!",
    }


@app.get("/api/task_status/{task_id}")
async def get_task_status(task_id: str):
    task_result = AsyncResult(task_id)
    if task_result.ready():
        if task_result.successful():
            return JSONResponse(
                content={
                    "status": "completed",
                    "result": task_result.result
                }
            )
        else:
            return JSONResponse(
                content={
                    "status": "failed",
                    "error": str(task_result.result)
                },
                status_code=500
            )
    else:
        return JSONResponse(
            content={
                "status": "in_progress"
            }
        )
        

@app.get("/getfile/{file_path:path}")
async def get_file(file_path: str):
    # Define the base directory where your video files are stored
    base_dir = BASE_DIR
    
    # Construct the full file path
    full_path = os.path.join(base_dir, file_path)
    
    # Check if the file exists
    if not os.path.isfile(full_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    # Check if the file is within the base directory (for security)
    if not os.path.abspath(full_path).startswith(os.path.abspath(base_dir)):
        raise HTTPException(status_code=403, detail="Access forbidden")
    
    # Return the file
    return FileResponse(full_path)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)


app.include_router(kb_router, prefix="/api/knowledge_base")
app.include_router(assistant_router, prefix="/api/assistant")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app)