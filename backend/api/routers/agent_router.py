from fastapi import APIRouter
from fastapi.responses import JSONResponse

from src.constants import ExistAgentType

agent_router = APIRouter()


@agent_router.get("")
async def get_agents():
    return JSONResponse(content={"agents": [agent.value for agent in ExistAgentType]})
