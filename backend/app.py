import os
from fastapi import FastAPI
from dotenv import load_dotenv
from api.routers import user_router, kb_router
from fastapi.responses import JSONResponse

load_dotenv()

BACKEND_PORT = int(os.getenv("BACKEND_PORT"))
RELOAD = os.getenv("MODE") == "development"

app = FastAPI(
    title="NoCodeAgentSystem",
)


@app.get("/", tags=["health_check"])
def health_check():
    return JSONResponse(status_code=200, content={"ping": "pong"})


app.include_router(user_router, tags=["user"], prefix="/api/users")
app.include_router(kb_router, tags=["knowledge_base"], prefix="/api/kb")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="0.0.0.0", port=BACKEND_PORT, reload=RELOAD)
