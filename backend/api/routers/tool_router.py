from fastapi import APIRouter
from fastapi.responses import JSONResponse
from src.constants import ExistTools

tool_router = APIRouter()


@tool_router.get("")
async def get_tools():
    return JSONResponse(content={"tools": [tool.value for tool in ExistTools]})
