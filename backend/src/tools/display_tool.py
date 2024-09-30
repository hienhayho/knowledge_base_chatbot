from api.utils.websocket_manager import ws_manager, MediaType, EndStatus, MessageType, Message
from llama_index.core.tools import FunctionTool
import asyncio
import os

def load_display_tool(conversation_id):

    def display_video(video_path: str):
        """
        Display the video at the given path.

        Parameters:
        - conversation_id (int): The ID of the conversation.
        - video_path (str): The path to the video file.

        Returns:
        - dict: The response message.
        """
        message = Message(
            message_type = MessageType.MESSAGE,
            media_type = MediaType.VIDEO,
            content = video_path,
            metadata = {
                "sender_type": "assistant",
                "file_name": os.path.basename(video_path)
            }
        )
        asyncio.run(ws_manager.send_chat_message(conversation_id, message))

        asyncio.run(ws_manager.send_end_message(
            conversation_id, MediaType.VIDEO, EndStatus.COMPLETE))
        return {"content": f"Displaying video at path: {video_path}"}

    return FunctionTool.from_defaults(display_video)