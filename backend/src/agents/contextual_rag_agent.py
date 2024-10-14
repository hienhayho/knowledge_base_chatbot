import sys
from pathlib import Path

from llama_index.core import Settings
from llama_index.llms.openai import OpenAI
from llama_index.agent.openai import OpenAIAgent
from llama_index.core.llms.function_calling import FunctionCallingLLM

sys.path.append(str(Path(__file__).parent.parent))
from src.constants import LLMService
from src.tools import load_kb_tool
from src.utils import get_formatted_logger
from src.settings import GlobalSettings, LLMCollection

logger = get_formatted_logger(__file__)


class ContextualRAGAgent:
    """
    Contextual RAG agent
    """

    def __init__(self, setting: GlobalSettings, collection_name: str) -> None:
        self.setting = setting
        self.collection_name = collection_name

        self.query_engine = self.create_query_engine()

        logger.info("ContextualRAGAgent for collection %s is ready", collection_name)

    def load_model(self, service: str, model_name: str) -> FunctionCallingLLM:
        """
        Load the LLM model

        Args:
            service (str): Service name
            model_name (str): Model name

        Returns:
            FunctionCallingLLM: Function calling LLM
        """
        if service == LLMService.OPENAI:
            return OpenAI(model=model_name)
        else:
            raise ValueError(f"Service {service} is not supported")

    def load_tools(self):
        """
        Load the tools
        """
        tools = [load_kb_tool(self.setting, collection_name=self.collection_name)]

        return tools

    def create_query_engine(self):
        """
        Create the query engine
        """
        self.llm = self.load_model(
            service=self.setting.llm_config.service,
            model_name=self.setting.llm_config.name,
        )
        Settings.llm = self.llm

        self.tools = self.load_tools()

        if self.setting.agent_config.type == LLMCollection.OPENAI:
            query_engine = OpenAIAgent.from_tools(
                tools=self.tools,
                llm=self.llm,
                verbose=True,
                system_prompt="You should answer in markdown format.",
            )

        else:
            raise ValueError(
                f"Agent type {self.setting.agent_config.type} not supported !"
            )

        return query_engine

    def chat(self, query: str):
        return self.query_engine.chat(query)
