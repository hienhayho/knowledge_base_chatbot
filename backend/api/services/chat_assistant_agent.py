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

from src.agents import CrewAIAgent
from src.settings import default_settings
from src.utils import get_formatted_logger
from src.tools import load_llama_index_kb_tool, load_product_search_tool
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
            instruct_prompt=self.configuration.instruct_prompt,
        ).strip("\n")

        self.tools = []

        for tool_name in self.configuration.tools:
            logger.info(
                f"Loading {tool_name}, description: {self.configuration.tools[tool_name]}"
            )
            if tool_name == ExistTools.KNOWLEDGE_BASE_QUERY:
                self.tools.append(
                    load_llama_index_kb_tool(
                        setting=default_settings,
                        kb_ids=self.configuration.kb_ids,
                        session_id=self.configuration.session_id,
                        is_contextual_rag=self.configuration.is_contextual_rag,
                        system_prompt=system_prompt,
                        description=self.configuration.tools[tool_name],
                    )
                )
            elif tool_name == ExistTools.PRODUCT_SEARCH:
                if self.configuration.file_product_path is None:
                    logger.warning(
                        f"Tool {tool_name} requires file_product_path to be set! But not found, so this tool will be ignored."
                    )
                    continue
                self.tools.append(
                    load_product_search_tool(
                        file_product_path=self.configuration.file_product_path,
                        description=self.configuration.tools[tool_name],
                    )
                )
            else:
                logger.warning(f"Tool {tool_name} is not supported yet!")
                continue

        kb_agent = Agent(
            role="Assistant",
            goal="Trả lời câu hỏi của người dùng",
            backstory=self.configuration.agent_backstory,
            llm=self.llm,
        )

        kb_task = Task(
            description="Phản hồi câu hỏi của khách hàng như sau: {query}.",
            expected_output="Một câu trả lời phù hợp nhất với câu hỏi của khách hàng.",
            agent=kb_agent,
            tools=[
                LlamaIndexTool.from_tool(tool, return_as_answer=True)
                for tool in self.tools
            ],
        )

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

        inputs = {
            "query": message,
        }
        response = self.agent.chat(inputs, message_history)

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
