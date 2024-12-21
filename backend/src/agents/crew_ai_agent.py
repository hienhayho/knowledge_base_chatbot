import os
import sys
from pathlib import Path

os.environ["CREWAI_TELEMETRY_OPT_OUT"] = "true"
os.environ["OTEL_SDK_DISABLED"] = "true"

sys.path.append(str(Path(__file__).parent.parent.parent))

from typing import Any, Type
from crewai import Agent, Crew, Task
from crewai.memory.entity.entity_memory import EntityMemory
from langchain_core.language_models.chat_models import BaseChatModel
from crewai.memory.short_term.short_term_memory import ShortTermMemory

from .memory_storage import QdrantStorage, EmbedderConfig
from src.settings import default_settings
from src.constants import embedding_dim
from src.utils import get_formatted_logger

logger = get_formatted_logger(__file__)


class CrewAIAgent:
    def __init__(
        self,
        agents: list[Agent],
        tasks: list[Task],
        manager_llm: Type[BaseChatModel],
        use_memory: bool = False,
        verbose: bool = True,
        conversation_id: str = None,
        embed_service: str = default_settings.embedding_config.service,
        embed_model: str = default_settings.embedding_config.name,
        quantize: bool = True,
    ):
        """
        Wrapper agent class for CrewAI.

        Args:
            agents (list[Agent]): List of agents from CrewAI

            tasks (list[Task]): List of tasks predefined

            manager_llm (Type[BaseChatModel]): Manager LLM. **IMPORTANT:** Now only support model from langchain

            use_memory (bool, optional): Use memory. Defaults to `False`.

            verbose (bool, optional): Verbose. Defaults to `True`.

            conversation_id (str, optional): Conversation ID. Defaults to `None`.

            embed_service (str, optional): Embedding service. Defaults to `default_settings.embedding_config.service`.

            embed_model (str, optional): Embedding model. Defaults to `default_settings.embedding_config.name`.

            quantize (bool, optional): Quantize the vectors before save to memory. Defaults to `True`.

        """
        self.agents = agents
        self.tasks = tasks
        self.manager_llm = manager_llm
        self.use_memory = use_memory
        self.verbose = verbose
        self.conversation_id = conversation_id
        self.embed_service = embed_service
        self.embed_model = embed_model
        self.quantize = quantize

        assert self.manager_llm is not None, "Manager LLM is required."

        if self.embed_model is not None:
            if self.embed_model not in embedding_dim:
                raise ValueError(
                    f"Unsupported embedding model: {self.embed_model}. Please add in the src/constants.py file."
                )

            self.vector_size = embedding_dim[self.embed_model]

        self.crew = self._get_crew()

    def _get_crew(self):
        """
        Get CrewAI Agent with or without memory.
        """

        logger.info("Initializing CrewAI Agent with memory: %s", self.use_memory)

        if self.use_memory:
            assert (
                self.conversation_id is not None
            ), "Conversation ID is required for creating memory storage."

            assert (
                self.embed_model is not None
            ), "Embedding model is required for creating memory storage."

            assert (
                self.embed_service is not None
            ), "Embedding service is required for creating memory storage."

            assert self.vector_size is not None, "Vector size is required."

            return Crew(
                agents=self.agents,
                tasks=self.tasks,
                memory=True,
                manager_llm=self.manager_llm,
                verbose=self.verbose,
                entity_memory=EntityMemory(
                    storage=QdrantStorage(
                        type=f"entity_memory_{self.conversation_id}",
                        url=default_settings.qdrant_config.url,
                        vector_size=self.vector_size,
                        quantize=self.quantize,
                        embedder_config=EmbedderConfig(
                            provider=self.embed_service,
                            config={
                                "model": self.embed_model,
                            },
                        ),
                    )
                ),
                short_term_memory=ShortTermMemory(
                    storage=QdrantStorage(
                        type=f"short_term_memory_{self.conversation_id}",
                        url=default_settings.qdrant_config.url,
                        vector_size=self.vector_size,
                        quantize=self.quantize,
                        embedder_config=EmbedderConfig(
                            provider=self.embed_service,
                            config={
                                "model": self.embed_model,
                            },
                        ),
                    )
                ),
            )

        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            manager_llm=self.manager_llm,
            verbose=self.verbose,
        )

    def chat(self, inputs: Any, *args, **kwargs) -> Any:
        return self.crew.kickoff(inputs=inputs).raw

    async def chat_async(self, inputs: Any, *args, **kwargs) -> Any:
        output = await self.crew.kickoff_async(inputs=inputs)
        return output.raw
