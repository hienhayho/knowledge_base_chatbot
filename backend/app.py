import os
import asyncio
from pathlib import Path
from pprint import pprint
from datetime import datetime
from dotenv import load_dotenv
from contextlib import asynccontextmanager
from fastapi.responses import JSONResponse
from fastapi import status, Request, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.utils import get_formatted_logger
from src.constants import DOWNLOAD_FOLDER, LOG_FOLDER
from api.routers import (
    user_router,
    kb_router,
    assistant_router,
    assistant_v2_router,
    tool_router,
    dashboard_router,
    admin_router,
)

logger = get_formatted_logger(__file__)

load_dotenv()


BACKEND_PORT = int(os.getenv("BACKEND_PORT"))
RELOAD = os.getenv("MODE") == "development"
CLEAN_INTERVAL = int(os.getenv("CLEAN_INTERVAL") or 10)
WORKERS = int(os.getenv("WORKERS") or 1)

pprint(
    {
        "BACKEND_PORT": BACKEND_PORT,
        "RELOAD": RELOAD,
        "CLEAN_INTERVAL": CLEAN_INTERVAL,
        "WORKERS": WORKERS,
    }
)


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

        await asyncio.sleep(CLEAN_INTERVAL * 60)


async def delete_log_files():
    while True:
        logger.warning("Cleaning up log folder ...")

        # 2 days
        interval = 2 * 24 * 60 * 60
        current_time = datetime.now()

        for file in Path(LOG_FOLDER).rglob("*"):
            try:
                if file.is_file():
                    file_mod_time = datetime.fromtimestamp(file.stat().st_mtime)
                    age = (current_time - file_mod_time).total_seconds()

                    if age > interval:
                        file.unlink()
                        logger.warning(f"Deleted file: {file}")
                    else:
                        logger.debug(f"Skipping file: {file}")
            except Exception as e:
                logger.error(f"Error deleting file {file}: {e}")

        # 1 day check interval
        await asyncio.sleep(24 * 60 * 60)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting application ...")
    logger.debug(f"Cleaning up download folder every {CLEAN_INTERVAL} minutes ...")
    asyncio.create_task(delete_old_files())
    logger.debug("Cleaning up log folder every 24 hours ...")
    asyncio.create_task(delete_log_files())
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


@app.middleware("http")
async def process_cookie_request(request: Request, call_next):
    cookie_values = request.cookies.get("CHATBOT_SSO")
    url = request.url.path

    if cookie_values:
        logger.debug(f"url: {url}, cookie: {cookie_values}")

        request.headers.__dict__["_list"].append(
            (
                "authorization".encode(),
                f"Bearer {cookie_values}".encode(),
            )
        )

    response = await call_next(request)
    return response


@app.get("/", tags=["health_check"], status_code=status.HTTP_200_OK)
def health_check():
    return JSONResponse(status_code=status.HTTP_200_OK, content={"ping": "pong"})


# Include routers
app.include_router(user_router, tags=["user"], prefix="/api/users")
app.include_router(kb_router, tags=["knowledge_base"], prefix="/api/kb")
app.include_router(assistant_router, tags=["assistant"], prefix="/api/assistant")
app.include_router(
    assistant_v2_router, tags=["assistant_v2"], prefix="/api/assistant_v2"
)
app.include_router(dashboard_router, tags=["dashboard"], prefix="/api/dashboard")
app.include_router(tool_router, tags=["tools"], prefix="/api/tools")
app.include_router(admin_router, tags=["admin"], prefix="/api/admin")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=BACKEND_PORT,
        reload=RELOAD,
        workers=WORKERS,
    )
