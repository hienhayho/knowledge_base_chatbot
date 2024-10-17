import uuid
from dotenv import load_dotenv
from llama_index.core import Settings
from langfuse.decorators import observe
from llama_index.llms.openai import OpenAI
from llama_index.agent.openai import OpenAIAgent
from llama_index.core.callbacks import CallbackManager
from langfuse.llama_index import LlamaIndexCallbackHandler
from llama_index.core.base.llms.types import ChatMessage as LLamaIndexChatMessage

from src.tools import load_kb_tool
from src.settings import default_settings
from src.utils import get_formatted_logger
from src.constants import ASSISTANT_SYSTEM_PROMPT, ChatAssistantConfig

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

        print(system_prompt)

        self.tools = [
            load_kb_tool(
                setting=default_settings,
                collection_name=self.configuration.collection_name,
                session_id=self.configuration.session_id,
                is_contextual_rag=self.configuration.is_contextual_rag,
                system_prompt=system_prompt,
            )
        ]

        self.agent = OpenAIAgent.from_tools(
            tools=self.tools,
            llm=self.llm,
            verbose=True,
            system_prompt=system_prompt,
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
            return OpenAI(
                model=model_id,
                temperature=self.configuration.temperature,
            )
        else:
            raise NotImplementedError(
                "The implementation for other types of LLMs are not ready yet!"
            )

    def on_message(self, message, message_history, session_id: str | uuid.UUID) -> str:
        langfuse_callback_handler.set_trace_params(
            session_id=str(session_id),
        )

        message_history = [
            LLamaIndexChatMessage(content=msg["content"], role=msg["role"])
            for msg in message_history
        ]
        response = self.agent.chat(message, message_history).response

        return response

    def stream_chat(self, message, message_history):
        message_history = [
            LLamaIndexChatMessage(content=msg["content"], role=msg["role"])
            for msg in message_history
        ]
        return self.agent.stream_chat(message, message_history).response_gen

    @observe
    async def astream_chat(self, message, message_history, session_id: str | uuid.UUID):
        langfuse_callback_handler.set_trace_params(
            name="astream_chat",
            session_id=str(session_id),
        )

        message_history = [
            LLamaIndexChatMessage(content=msg["content"], role=msg["role"])
            for msg in message_history
        ]
        response = await self.agent.astream_chat(message, message_history)

        return response
