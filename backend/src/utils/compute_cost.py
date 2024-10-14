import os
import requests
from uuid import UUID
from dotenv import load_dotenv
from .logger import get_formatted_logger

load_dotenv()

LANGFUSE_HOST = os.getenv("LANGFUSE_HOST")
LANGFUSE_PUBLIC_KEY = os.getenv("LANGFUSE_PUBLIC_KEY")
LANGFUSE_SECRET_KEY = os.getenv("LANGFUSE_SECRET_KEY")


logger = get_formatted_logger(__file__)


def get_cost_from_trace_id(trace_id: str | UUID) -> float:
    """
    Get cost from trace ID from Langfuse

    Args:
        trace_id (str | UUID): The trace ID

    Returns:
        float: The total cost of the trace ID provided
    """
    trace_id = str(trace_id)

    url = f"{LANGFUSE_HOST}/api/public/traces/{trace_id}"
    response = requests.get(url, auth=(LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY))

    if response.status_code != 200:
        logger.error(
            f"Failed to get cost for trace ID: {trace_id}, status code: {response.status_code}, response: {response.text}. So returning 0.0"
        )
        return 0.0

    data = response.json()

    if "totalCost" not in data:
        logger.warning(
            f"Failed to get cost for trace ID: {trace_id}, response: {response.text}. So returning 0.0"
        )
        return 0.0

    return data["totalCost"]


def get_cost_from_session_id(session_id: str | UUID) -> float:
    """
    Get cost from session ID from Langfuse

    Args:
        session_id (str | UUID): The session ID (conversations.id)

    Returns:
        float: The total cost of all traces in the session
    """
    session_id = str(session_id)

    logger.debug(f"Getting cost for session ID: {session_id}")

    url = f"{LANGFUSE_HOST}/api/public/sessions/{session_id}"
    response = requests.get(url, auth=(LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY))

    if response.status_code != 200:
        logger.warning(
            f"Failed to get cost for session ID: {session_id}, status code: {response.status_code}, response: {response.text}. So returning 0.0"
        )
        return 0.0

    data = response.json()

    if len(data["traces"]) == 0:
        logger.debug(f"No traces found for session ID: {session_id}. So returning 0.0")
        return 0.0

    return sum([get_cost_from_trace_id(item["id"]) for item in data["traces"]])
