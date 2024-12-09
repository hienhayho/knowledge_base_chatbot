import uuid
from crewai import Agent, Task
from dotenv import load_dotenv
from llama_index.core import Settings
from langfuse.decorators import observe
from langchain_openai import ChatOpenAI
from llama_index.core.callbacks import CallbackManager
from langfuse.llama_index import LlamaIndexCallbackHandler
from llama_index.core.base.llms.types import ChatMessage as LLamaIndexChatMessage
from crewai_tools import LlamaIndexTool

from src.tools import load_llama_index_kb_tool
from src.agents import CrewAIAgent
from src.settings import default_settings
from src.utils import get_formatted_logger
from src.constants import (
    ASSISTANT_SYSTEM_PROMPT,
    ChatAssistantConfig,
    MesssageHistory,
    ExistTools,
)

logger = get_formatted_logger(__file__)
load_dotenv()

langfuse_callback_handler = LlamaIndexCallbackHandler()
Settings.callback_manager = CallbackManager([langfuse_callback_handler])


class ChatAssistant:
    def __init__(self, configuration: ChatAssistantConfig):
        self.configuration = configuration
        self._init_agent()

    def _init_agent(self):
        model_name = self.configuration.model
        service = self.configuration.service

        self.llm = self._init_model(service, model_name)

        system_prompt = ASSISTANT_SYSTEM_PROMPT.format(
            interested_prompt=self.configuration.interested_prompt,
            guard_prompt=self.configuration.guard_prompt,
        ).strip("\n")

        self.tools = []

        for tool_name in self.configuration.tools:
            if tool_name == ExistTools.KB_TOOL:
                self.tools.append(
                    load_llama_index_kb_tool(
                        setting=default_settings,
                        kb_ids=self.configuration.kb_ids,
                        session_id=self.configuration.session_id,
                        is_contextual_rag=self.configuration.is_contextual_rag,
                        system_prompt=system_prompt,
                    )
                )
            else:
                logger.warning(f"Tool {tool_name} is not supported yet!")
                continue

        # kb_search_tool = KBSearchTool(
        #     kb_ids=self.configuration.kb_ids,
        #     contextual_rag=ContextualRAG.from_setting(default_settings),
        #     session_id=self.configuration.session_id,
        #     is_contextual_rag=self.configuration.is_contextual_rag,
        #     system_prompt=system_prompt,
        #     result_as_answer=True,
        # )

        # crewai_kb_search_tool = CrewAIStructuredTool().from_function(
        #     kb_search_tool._run,
        #     name=kb_search_tool.name,
        #     description=kb_search_tool.description,
        #     args_schema=kb_search_tool.args_schema,
        #     return_direct=True,
        # )

        kb_agent = Agent(
            role="Assistant",
            goal="Trả lời câu hỏi của người dùng",
            # backstory="""
            # Bạn là một nhân viên chăm sóc khách hàng chuyên nghiệp và thân thiện của công ty Quang Nhật. Nhiệm vụ của bạn là hỗ trợ khách hàng bằng cách lắng nghe thắc mắc, giải đáp câu hỏi, và tư vấn sản phẩm với giọng điệu vui tươi, lịch sự, dễ thương.
            # - Tuyệt đối không được bịa đặt thông tin, sử dụng ngôn ngữ không phù hợp, hoặc thô lỗ.
            # - Bạn hãy xưng hô anh hoặc chị dựa theo cuộc trò chuyện với khách hàng.
            # - Sử dụng từ ngữ như “dạ, vâng” trong câu trả lời để thể hiện sự chuyên nghiệp.
            # - Khi được hỏi về sản phẩm bán chạy thì bạn trả lời FPT Camera.
            # Khi được hỏi về những sản phẩm của công ty như:
            # - Bên em có những sp gì?
            # - Sản phẩm bên em có gì?
            # - Bên em bán những gì?
            # thì bạn hãy trả lời:"Những sản phẩm của công ty Quang Nhật bao gồm các bảng điều khiển, các bộ phận cảm biến, các loại công tắc, các loại đèn led, sản phẩm FPT camera, FPT camera play, các loại khóa cửa, các loại ổ cắm, các loại nút bấm, FPT play box, thiết bị mở rộng sóng zigbee
            # Hướng dẫn xử lý yêu cầu của khách hàng:
            # 1. **Thông tin chung và chính sách**
            #    - Sử dụng **knowledge_base_query**
            #    - Bao gồm: thông tin liên hệ, smart home, ổ cắm thông minh,  thông tin lắp đặt, tiện ích giải pháp smart home, hướng dẫn nghiệp vụ (tính toán, giải thích,...), thông tin các thiết bị (cảm biến, đèn led, động cơ rèm, cửa tự động), giải pháp an ninh, giải pháp tiết kiệm điện, truyền hình, thông tin giỏ hàng, chương trình khuyến mãi, thông tin lắp đặt, ý tưởng thiết kế.
            #    - Với thông tin mà bạn không biết thì bạn hãy trả lời:"Với câu hỏi này hiện em chưa trả lời được. Anh/chị có thể cung cấp số điện thoại để em có thể hỗ trợ trả lời sau được không ạ?"
            # "
            #             """,
            backstory=self.configuration.agent_backstory,
            llm=self.llm,
        )

        kb_task = Task(
            description="Phản hồi câu hỏi của khách hàng như sau: {query}.",
            expected_output="Một câu trả lời phù hợp nhất với câu hỏi của khách hàng.",
            agent=kb_agent,
            tools=[
                # kb_search_tool,
                LlamaIndexTool.from_tool(tool, return_as_answer=True)
                for tool in self.tools
                # crewai_kb_search_tool
            ],
        )

        # self.agent = OpenAIAgent.from_tools(
        #     tools=self.tools,
        #     llm=self.llm,
        #     verbose=True,
        # )

        self.agent = CrewAIAgent(
            agents=[kb_agent],
            tasks=[kb_task],
            manager_llm=self.llm,
            verbose=True,
            conversation_id=self.configuration.conversation_id,
        )

    def _init_model(self, service, model_id):
        """
        Select a model for text generation using multiple services.
        Args:
            service (str): Service name indicating the type of model to load.
            model_id (str): Identifier of the model to load from HuggingFace's model hub.
        Returns:
            LLM: llama-index LLM for text generation
        Raises:
            ValueError: If an unsupported model or device type is provided.
        """
        logger.info(f"Loading Model: {model_id}")
        logger.info("This action can take a few minutes!")
        # TODO: setup proper logging

        if service == "openai":
            logger.info(f"Loading OpenAI Model: {model_id}")
            # return OpenAI(
            #     model=model_id,
            #     temperature=self.configuration.temperature,
            # )
            return ChatOpenAI(
                model=model_id,
                temperature=self.configuration.temperature,
            )
        else:
            raise NotImplementedError(
                "The implementation for other types of LLMs are not ready yet!"
            )

    @observe()
    def on_message(
        self,
        message: str,
        message_history: list[MesssageHistory],
        session_id: str | uuid.UUID,
    ) -> str:
        langfuse_callback_handler.set_trace_params(
            session_id=str(session_id),
        )

        # message_history = [
        #     LLamaIndexChatMessage(content=msg.content, role=msg.role)
        #     for msg in message_history
        # ]
        inputs = {
            "query": message,
        }
        # response = self.agent.chat(message, message_history).response
        response = self.agent.chat(inputs, message_history)

        print("response: ", response)

        return response

    def stream_chat(self, message: str, message_history: list[MesssageHistory]):
        message_history = [
            LLamaIndexChatMessage(content=msg["content"], role=msg["role"])
            for msg in message_history
        ]
        return self.agent.stream_chat(message, message_history).response_gen

    @observe()
    async def astream_chat(
        self,
        message: str,
        message_history: list[MesssageHistory],
        session_id: str | uuid.UUID,
    ):
        langfuse_callback_handler.set_trace_params(
            name="astream_chat",
            session_id=str(session_id),
        )

        message_history = [
            LLamaIndexChatMessage(content=msg.content, role=msg.role)
            for msg in message_history
        ]
        response = await self.agent.astream_chat(message, message_history)

        return response
