from fastapi import APIRouter, HTTPException, Depends, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from typing import List, AsyncGenerator, Generator
from api.models.assistant import AssistantCreate, AssistantResponse, ChatMessage, ChatResponse, ConversationResponse, MessageResponse
from api.services.assistant import AssistantService
from api.utils.websocket_manager import ws_manager, MediaType, EndStatus
from src.dependencies import get_current_user_id
import logging

assistant_router = APIRouter()

## Assistant ##
@assistant_router.post("/", response_model=AssistantResponse)
async def create_assistant(
    assistant: AssistantCreate,
    current_user_id: int = Depends(get_current_user_id),
    assistant_service: AssistantService = Depends()
):
    return assistant_service.create_assistant(current_user_id, assistant)

@assistant_router.get("/", response_model=List[AssistantResponse])
async def get_all_assistants(
    current_user_id: int = Depends(get_current_user_id),
    assistant_service: AssistantService = Depends()
):
    return assistant_service.get_all_assistants(current_user_id)

@assistant_router.get("/{assistant_id}", response_model=AssistantResponse)
async def get_assistant(
    assistant_id: int,
    current_user_id: int = Depends(get_current_user_id),
    assistant_service: AssistantService = Depends()
):
    assistant = assistant_service.get_assistant(assistant_id, current_user_id)
    if assistant is None:
        raise HTTPException(status_code=404, detail="Assistant not found")
    return assistant

@assistant_router.delete("/{assistant_id}", response_model=dict)
async def delete_assistant(
    assistant_id: int,
    current_user_id: int = Depends(get_current_user_id),
    assistant_service: AssistantService = Depends()
):
    success = assistant_service.delete_assistant(assistant_id, current_user_id)
    if not success:
        raise HTTPException(status_code=404, detail="Assistant not found")
    return {"message": "Assistant deleted successfully"}


### Conversations ###
@assistant_router.get("/{assistant_id}/conversations", response_model=List[ConversationResponse])
async def get_assistant_conversations(
    assistant_id: int,
    current_user_id: int = Depends(get_current_user_id),
    assistant_service: AssistantService = Depends()
):
    conversations = assistant_service.get_assistant_conversations(assistant_id, current_user_id)
    if conversations is None:
        raise HTTPException(status_code=404, detail="Assistant not found")
    return conversations

@assistant_router.post("/{assistant_id}/conversations", response_model=ConversationResponse)
async def create_conversation(
    assistant_id: int,
    current_user_id: int = Depends(get_current_user_id),
    assistant_service: AssistantService = Depends()
):
    return assistant_service.create_conversation(current_user_id, assistant_id)

@assistant_router.post("/{assistant_id}/conversations/{conversation_id}/chat", response_model=ChatResponse)
async def chat_with_assistant(
    assistant_id: int,
    conversation_id: int,
    message: ChatMessage,
    current_user_id: int = Depends(get_current_user_id),
    assistant_service: AssistantService = Depends()
):
    return assistant_service.chat_with_assistant(conversation_id, current_user_id, message)

@assistant_router.post("/{assistant_id}/conversations/{conversation_id}/chat/stream")
async def stream_chat_with_assistant(
    assistant_id: int,
    conversation_id: int,
    message: ChatMessage,
    current_user_id: int = Depends(get_current_user_id),
    assistant_service: AssistantService = Depends()
) -> StreamingResponse:
    def event_generator() -> Generator[str, None, None]:
        for chunk in assistant_service.stream_chat_with_assistant(conversation_id, current_user_id, message):
            yield chunk

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@assistant_router.get("/{assistant_id}/conversations/{conversation_id}/history", response_model=List[MessageResponse])
async def get_conversation_history(
    assistant_id: int,
    conversation_id: int,
    current_user_id: int = Depends(get_current_user_id),
    assistant_service: AssistantService = Depends()
):
    return assistant_service.get_conversation_history(conversation_id, current_user_id)


@assistant_router.websocket("/{assistant_id}/conversations/{conversation_id}/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    assistant_id: int,
    conversation_id: int,
    current_user_id: int = Depends(get_current_user_id),
    assistant_service: AssistantService = Depends()
):
    await ws_manager.connect(conversation_id, websocket)
    try:
        while True:
            data = await websocket.receive_json()
            
            # Send acknowledgement of received message
            await ws_manager.send_status(conversation_id, "message_received")

            # Process the incoming message
            message = ChatMessage(content=data["content"])
            
            try:
                async for chunk in assistant_service.astream_chat_with_assistant(conversation_id, current_user_id, message):
                    # Assume chunk is a string. If it's a different structure, adjust accordingly.
                    await ws_manager.send_text_message(
                        conversation_id,
                        chunk,
                        sender_type="assistant",
                        extra_metadata={"assistant_id": assistant_id}
                    )

                # Send end message for successful completion
                await ws_manager.send_end_message(
                    conversation_id,
                    MediaType.TEXT,
                    EndStatus.COMPLETE,
                    {"assistant_id": assistant_id}
                )

            except Exception as e:
                # Handle any errors during message processing
                error_message = f"Error processing message: {str(e)}"
                await ws_manager.send_error(conversation_id, error_message)
                await ws_manager.send_end_message(
                    conversation_id,
                    MediaType.TEXT,
                    EndStatus.ERROR,
                    {"error_message": error_message, "assistant_id": assistant_id}
                )

    except WebSocketDisconnect:
        # Handle WebSocket disconnect
        ws_manager.disconnect(conversation_id)
        # You might want to log this disconnect or perform any cleanup
        logging.info(f"WebSocket disconnected for conversation {conversation_id}")

    except Exception as e:
        # Handle any other unexpected errors
        error_message = f"Unexpected error in WebSocket connection: {str(e)}"
        await ws_manager.send_error(conversation_id, error_message)
        await ws_manager.send_end_message(
            conversation_id,
            MediaType.TEXT,
            EndStatus.ERROR,
            {"error_message": error_message, "assistant_id": assistant_id}
        )
        ws_manager.disconnect(conversation_id)