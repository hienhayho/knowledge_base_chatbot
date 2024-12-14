import os
import sys
from pathlib import Path

os.environ["CREWAI_TELEMETRY_OPT_OUT"] = "true"
os.environ["OTEL_SDK_DISABLED"] = "true"

sys.path.append(str(Path(__file__).parent.parent.parent))

from typing import Any
from crewai import Agent, Crew, Task
from crewai.memory.entity.entity_memory import EntityMemory
from crewai.memory.short_term.short_term_memory import ShortTermMemory

from .memory_storage import QdrantStorage, EmbedderConfig
from src.settings import default_settings
from src.constants import embedding_dim


class CrewAIAgent:
    def __init__(
        self,
        agents: list[Agent],
        tasks: list[Task],
        manager_llm: str,
        verbose: bool = True,
        conversation_id: str = None,
        embed_service: str = default_settings.embedding_config.service,
        embed_model: str = default_settings.embedding_config.name,
    ):
        self.agents = agents
        self.tasks = tasks
        self.manager_llm = manager_llm
        self.verbose = verbose
        self.conversation_id = conversation_id
        self.embed_service = embed_service
        self.embed_model = embed_model

        if self.embed_model not in embedding_dim:
            raise ValueError(
                f"Unsupported embedding model: {self.embed_model}. Please add in the src/constants.py file."
            )

        self.vector_size = embedding_dim[self.embed_model]

        self.crew = self.get_crew()

    def get_crew(self):
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
                    quantize=True,
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
                    quantize=True,
                    embedder_config=EmbedderConfig(
                        provider=self.embed_service,
                        config={
                            "model": self.embed_model,
                        },
                    ),
                )
            ),
        )

    def chat(self, inputs: Any, *args, **kwargs) -> Any:
        return self.crew.kickoff(inputs=inputs).raw
