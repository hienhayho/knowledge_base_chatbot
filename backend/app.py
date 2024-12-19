import os
import asyncio
from pathlib import Path
from fastapi import status
from fastapi import FastAPI
from datetime import datetime
from dotenv import load_dotenv
from src.utils import get_formatted_logger
from src.constants import DOWNLOAD_FOLDER
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from api.routers import (
    user_router,
    kb_router,
    assistant_router,
    tool_router,
    dashboard_router,
    admin_router,
)
from contextlib import asynccontextmanager

logger = get_formatted_logger(__file__)

load_dotenv()

CLEAN_INTERVAL = int(os.getenv("CLEAN_INTERVAL") or 10)


async def delete_old_files():
    while True:
        logger.warning("Cleaning up download folder ...")

        interval = 20
        current_time = datetime.now()

        for file in Path(DOWNLOAD_FOLDER).iterdir():
            try:
                if file.is_file():
                    file_mod_time = datetime.fromtimestamp(file.stat().st_mtime)
                    age = (current_time - file_mod_time).total_seconds()

                    if age > interval:
                        file.unlink()
                        logger.warning(f"Deleted file: {file}")
                    else:
                        logger.info(f"Skipping file: {file}")
            except Exception as e:
                logger.error(f"Error deleting file {file}: {e}")

        await asyncio.sleep(5 * 60)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting application ...")
    logger.debug(f"Cleaning up download folder every {CLEAN_INTERVAL} minutes ...")
    asyncio.create_task(delete_old_files())
    yield

    logger.info("Shutting down application ...")


app = FastAPI(
    title="Knowledge Base Chatbot",
    contact={"name": "hienhayho", "email": "hienhayho3002@gmail.com"},
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["health_check"], status_code=status.HTTP_200_OK)
def health_check():
    return JSONResponse(status_code=status.HTTP_200_OK, content={"ping": "pong"})


# Include routers
app.include_router(user_router, tags=["user"], prefix="/api/users")
app.include_router(kb_router, tags=["knowledge_base"], prefix="/api/kb")
app.include_router(assistant_router, tags=["assistant"], prefix="/api/assistant")
app.include_router(dashboard_router, tags=["dashboard"], prefix="/api/dashboard")
app.include_router(tool_router, tags=["tools"], prefix="/api/tools")
app.include_router(admin_router, tags=["admin"], prefix="/api/admin")
