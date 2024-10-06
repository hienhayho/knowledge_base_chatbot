from dotenv import load_dotenv
from src.tools import load_kb_tool
from src.settings import defaul_settings
from llama_index.core.base.llms.types import ChatMessage as LLamaIndexChatMessage
from llama_index.llms.openai import OpenAI
from llama_index.agent.openai import OpenAIAgent
from .prompt import ASSISTANT_SYSTEM_PROMPT
from src.utils import get_formatted_logger

logger = get_formatted_logger(__file__)
load_dotenv()


class ChatAssistant:
    def __init__(self, configuration: dict):
        self.configuration = configuration
        self._init_agent()

    def _init_agent(self):
        model_name = self.configuration.get("model")
        service = self.configuration.get("service")

        self.llm = self._init_model(service, model_name)
        self.tools = [
            load_kb_tool(
                defaul_settings,
                self.configuration.get("collection_name"),
                self.configuration.get("is_contextual_rag"),
            )
        ]

        self.agent = OpenAIAgent.from_tools(
            tools=self.tools,
            llm=self.llm,
            verbose=True,
            system_prompt=ASSISTANT_SYSTEM_PROMPT,
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
                temperature=self.configuration["temperature"],
            )
        else:
            raise NotImplementedError(
                "The implementation for other types of LLMs are not ready yet!"
            )

    def on_message(self, message, message_history) -> str:
        message_history = [
            LLamaIndexChatMessage(content=msg["content"], role=msg["role"])
            for msg in message_history
        ]
        return self.agent.chat(message, message_history)

    def stream_chat(self, message, message_history):
        message_history = [
            LLamaIndexChatMessage(content=msg["content"], role=msg["role"])
            for msg in message_history
        ]
        return self.agent.stream_chat(message, message_history).response_gen

    async def astream_chat(self, message, message_history):
        message_history = [
            LLamaIndexChatMessage(content=msg["content"], role=msg["role"])
            for msg in message_history
        ]
        response = await self.agent.astream_chat(message, message_history)
        return response
