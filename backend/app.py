import os
import asyncio
from pathlib import Path
from fastapi import FastAPI
from datetime import datetime
from dotenv import load_dotenv
from src.utils import get_formatted_logger
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from api.routers import user_router, kb_router, assistant_router, DOWNLOAD_FOLDER
from contextlib import asynccontextmanager

logger = get_formatted_logger(__file__)

load_dotenv()

BACKEND_PORT = int(os.getenv("BACKEND_PORT"))
RELOAD = os.getenv("MODE") == "development"


# Define the lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup event
    asyncio.create_task(delete_old_files())
    yield
    # Shutdown event (if you need to do something during shutdown)
    logger.info("Shutting down application ...")


app = FastAPI(
    title="NoCodeAgentSystem",
    lifespan=lifespan,  # Using lifespan instead of on_event
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Background task to delete old files
async def delete_old_files():
    while True:
        logger.warning("Cleaning up download folder ...")
        interval = 20  # seconds
        current_time = datetime.now()

        for file in Path(DOWNLOAD_FOLDER).iterdir():
            if file.is_file():  # Only process files, not directories
                file_mod_time = datetime.fromtimestamp(file.stat().st_mtime)
                age = (current_time - file_mod_time).total_seconds()

                if age > interval:
                    try:
                        file.unlink()
                        logger.info(f"Deleted file: {file}")
                    except Exception as e:
                        logger.error(f"Error deleting file {file}: {e}")
                else:
                    logger.info(f"Skipping file: {file}")

        await asyncio.sleep(120)  # Wait for 120 seconds before the next run


@app.get("/", tags=["health_check"])
def health_check():
    return JSONResponse(status_code=200, content={"ping": "pong"})


# Include routers
app.include_router(user_router, tags=["user"], prefix="/api/users")
app.include_router(kb_router, tags=["knowledge_base"], prefix="/api/kb")
app.include_router(assistant_router, tags=["assistant"], prefix="/api/assistant")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="0.0.0.0", port=BACKEND_PORT, reload=RELOAD)
