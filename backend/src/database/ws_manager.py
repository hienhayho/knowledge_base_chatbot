import sys
from uuid import UUID
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

import base64
from enum import Enum
from fastapi import WebSocket
from typing import Dict, Any, Optional
from src.utils import get_formatted_logger

logger = get_formatted_logger(__file__)

END_TOKEN = "<END>"


class MediaType(str, Enum):
    TEXT = "text"
    VIDEO = "video"
    AUDIO = "audio"
    IMAGE = "image"


class MessageType(str, Enum):
    MESSAGE = "message"
    STATUS = "status"
    ERROR = "error"
    END = "end"


class EndStatus(str, Enum):
    COMPLETE = "complete"
    INTERRUPTED = "interrupted"
    ERROR = "error"
    TIMEOUT = "timeout"


class Message:
    def __init__(
        self,
        message_type: MessageType,
        media_type: MediaType,
        content: Any,
        metadata: Dict[str, Any],
    ):
        self.message_type = message_type
        self.media_type = media_type
        self.content = content
        self.metadata = metadata

    def to_dict(self):
        payload = {
            "type": self.message_type,
            "media_type": self.media_type,
            "metadata": self.metadata,
        }

        if isinstance(self.content, bytes):
            payload["content"] = base64.b64encode(self.content).decode("utf-8")
        else:
            payload["content"] = self.content

        return payload


class WsManager:
    def __init__(self):
        logger.info("WebSocket Manager initialized successfully !!!")
        self.active_connections: Dict[int, WebSocket] = {}

    async def connect(self, conversation_id: int, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[conversation_id] = websocket

    def disconnect(self, conversation_id: int):
        self.active_connections.pop(conversation_id, None)

    async def send_chat_message(self, conversation_id: UUID, message: Message):
        if websocket := self.active_connections.get(conversation_id):
            await websocket.send_json(message.to_dict())

    async def send_text_message(
        self,
        conversation_id: UUID,
        text: str,
        sender_type: str = "assistant",
        extra_metadata: Optional[Dict[str, Any]] = None,
    ):
        metadata = {"sender_type": sender_type, **(extra_metadata or {})}
        message = Message(
            message_type=MessageType.MESSAGE,
            media_type=MediaType.TEXT,
            content=text,
            metadata=metadata,
        )
        await self.send_chat_message(conversation_id, message)

    async def send_media_chunk(
        self,
        conversation_id: int,
        media_type: MediaType,
        chunk: bytes,
        chunk_metadata: Dict[str, Any],
    ):
        message = Message(
            message_type=MessageType.MESSAGE,
            media_type=media_type,
            content=chunk,
            metadata=chunk_metadata,
        )
        await self.send_chat_message(conversation_id, message)

    async def send_status(
        self,
        conversation_id: int,
        status: str,
        extra_metadata: Optional[Dict[str, Any]] = None,
    ):
        metadata = {"status": status, **(extra_metadata or {})}
        message = Message(
            message_type=MessageType.STATUS,
            media_type=MediaType.TEXT,
            content=status,
            metadata=metadata,
        )
        await self.send_chat_message(conversation_id, message)

    async def send_error(
        self,
        conversation_id: UUID,
        error_message: str,
        extra_metadata: Optional[Dict[str, Any]] = None,
    ):
        metadata = {"error": error_message, **(extra_metadata or {})}
        message = Message(
            message_type=MessageType.ERROR,
            media_type=MediaType.TEXT,
            content=error_message,
            metadata=metadata,
        )
        await self.send_chat_message(conversation_id, message)

    async def send_end_message(
        self,
        conversation_id: int,
        media_type: MediaType,
        end_status: EndStatus,
        extra_metadata: Optional[Dict[str, Any]] = None,
    ):
        metadata = {
            "end_token": END_TOKEN,
            "end_status": end_status,
            **(extra_metadata or {}),
        }
        message = Message(
            message_type=MessageType.END,
            media_type=media_type,
            content=f"{media_type}_end",
            metadata=metadata,
        )
        await self.send_chat_message(conversation_id, message)


def get_ws_manager():
    return WsManager()
