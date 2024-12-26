import re
import time
from uuid import UUID
from typing import Annotated
from sqlmodel import Session, select, desc
from fastapi import APIRouter, Depends, HTTPException, status, Body

from api.models import ChatMessage
from .user_router import get_current_user
from api.services import AssistantService
from src.constants import ApiResponse, SenderType
from src.database import get_session, Users, Assistants, Conversations, Messages
from src.utils import get_formatted_logger

logger = get_formatted_logger(__file__, file_path="logs/assistant_v2_router.log")

assistant_v2_router = APIRouter()


@assistant_v2_router.post("/conversation")
async def create_conversation(
    current_user: Annotated[Users, Depends(get_current_user)],
    db_session: Annotated[Session, Depends(get_session)],
):
    with db_session as session:
        assistant = session.exec(
            select(Assistants).where(Assistants.user_id == current_user.id)
        ).first()

        if not assistant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Assistant not found"
            )

        new_conversation = Conversations(
            assistant_id=assistant.id, user_id=current_user.id
        )
        session.add(new_conversation)
        session.commit()
        session.refresh(new_conversation)

        welcome_message_template = "Xin chào anh/chị. Em là nhân viên hỗ trợ tư vấn của {organization}. Anh/chị cần giúp đỡ hoặc có câu hỏi gì không ạ ?"

        welcome_message = welcome_message_template.format(
            organization=current_user.organization
        )

        if "vndc" in current_user.organization.lower():
            welcome_message = "Xin chào bạn, tôi là Chương, trợ lý ảo từ công ty VNDC, xin hỏi tôi có thể giúp gì cho bạn?"

        new_message = Messages(
            conversation_id=new_conversation.id,
            content=welcome_message,
            sender_type=SenderType.ASSISTANT,
        )

        session.add(new_message)
        session.commit()
        session.refresh(new_message)

        return ApiResponse(
            status_code=0,
            status_message="Successfully!",
            http_code=status.HTTP_200_OK,
            data={
                **new_conversation.model_dump(),
                "text": welcome_message,
            },
        )


@assistant_v2_router.get("/conversations")
async def get_assistant_conversations(
    current_user: Annotated[Users, Depends(get_current_user)],
    db_session: Annotated[Session, Depends(get_session)],
):
    with db_session as session:
        query = select(Assistants).where(Assistants.user_id == current_user.id)

        assistant = session.exec(query).first()
        if not assistant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Assistant not found"
            )

        query = (
            select(Conversations)
            .where(Conversations.assistant_id == assistant.id)
            .order_by(desc(Conversations.updated_at))
        )
        conversations = session.exec(query).all()
        return conversations


@assistant_v2_router.post(
    "/conversations/{conversation_id}/production_messages",
    response_model=ApiResponse,
)
async def production_send_message(
    conversation_id: UUID,
    message: Annotated[ChatMessage, Body(...)],
    current_user: Annotated[Users, Depends(get_current_user)],
    assistant_service: Annotated[AssistantService, Depends()],
    db_session: Annotated[Session, Depends(get_session)],
):
    with db_session as session:
        assistant = session.exec(
            select(Assistants).where(Assistants.user_id == current_user.id)
        ).first()

        if not assistant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Assistant not found"
            )

        conversation_id = str(conversation_id)

        start_time = time.time()
        result = await assistant_service.achat_with_assistant(
            conversation_id,
            current_user.id,
            message=message,
            start_time=start_time,
            use_parser=True,
        )

        for product in result["products"]:
            if product["price"]:
                try:
                    logger.debug(f"Try to parse with llm json_mode: {product['price']}")
                    product["price"] = "{:,.0f} đ".format(product["price"]).replace(
                        ",", "."
                    )
                except Exception as e:
                    logger.error(f"Error when formatting with llm json_mode: {str(e)}")
                    logger.debug(
                        f"Product: {product}",
                    )
                    price = re.sub(r"\D", "", f"{product["price"]}")
                    try:
                        logger.debug("Try to using regex to get price: ", price)
                        product["price"] = "{:,.0f} đ".format(int(price)).replace(
                            ",", "."
                        )
                    except Exception as e:
                        logger.error(
                            f"Error when formatting with regex: {price}, {str(e)}"
                        )
                        logger.debug("Use default option...")
                        product["price"] = "Liên hệ"
            else:
                product["price"] = "Liên hệ"

        logger.info("=" * 100)

        return ApiResponse(
            data=result,
            status_message="Successfully!",
            http_code=status.HTTP_200_OK,
            status_code=0,
            extra_info={
                "respone_time": time.time() - start_time,
            },
        )
