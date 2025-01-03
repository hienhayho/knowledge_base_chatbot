import uuid
from crewai import Agent, Task
from dotenv import load_dotenv
from llama_index.core import Settings
from llama_index.llms.openai import OpenAI
from llama_index.core.tools import FunctionTool
from llama_index.agent.openai import OpenAIAgent
from llama_index.core.callbacks import CallbackManager
from llama_index.core.base.llms.types import ChatMessage as LLamaIndexChatMessage

from langfuse.decorators import observe
from langchain_openai import ChatOpenAI
from langfuse.llama_index import LlamaIndexCallbackHandler

from src.agents import CrewAIAgent
from src.settings import default_settings
from src.utils import get_formatted_logger
from src.tools import load_llama_index_kb_tool, load_product_search_tool, LlamaIndexTool
from src.constants import (
    ASSISTANT_SYSTEM_PROMPT,
    ChatAssistantConfig,
    MesssageHistory,
    ExistTools,
    ExistAgentType,
)

logger = get_formatted_logger(__file__, file_path="logs/chat_assistant/log.log")
load_dotenv()

langfuse_callback_handler = LlamaIndexCallbackHandler()
Settings.callback_manager = CallbackManager([langfuse_callback_handler])


class ChatAssistant:
    """
    Main ChatAssistant class to handle the chat with user.
    """

    def __init__(self, configuration: ChatAssistantConfig):
        self.configuration = configuration
        self._init_agent()

    def _init_agent(self):
        """
        Initialize the agent with the given configuration.
        """

        agent_type = self.configuration.agent_type
        logger.info(f"Initializing agent with type: {agent_type}")

        if agent_type == ExistAgentType.CREWAI_AGENT:
            self.agent = self._init_crewai_agent()
        elif agent_type == ExistAgentType.OPENAI_AGENT:
            self.agent = self._init_openai_agent()

    def _init_crewai_agent(self):
        model_name = self.configuration.model
        service = self.configuration.service

        llm = self._init_langchain_model(service, model_name)

        system_prompt = ASSISTANT_SYSTEM_PROMPT.format(
            instruct_prompt=self.configuration.instruct_prompt,
        ).strip("\n")

        tools: list[FunctionTool] = []
        return_as_answer_flags: list[bool] = []

        for tool_name in self.configuration.tools:
            description = self.configuration.tools[tool_name]["description"]
            return_as_answer = self.configuration.tools[tool_name]["return_as_answer"]

            logger.info(
                {
                    "tool_name": tool_name,
                    "return_as_answer": return_as_answer,
                    "description": description,
                },
            )

            if tool_name == ExistTools.KNOWLEDGE_BASE_QUERY:
                tools.append(
                    load_llama_index_kb_tool(
                        setting=default_settings,
                        kb_ids=self.configuration.kb_ids,
                        session_id=self.configuration.session_id,
                        is_contextual_rag=self.configuration.is_contextual_rag,
                        system_prompt=system_prompt,
                        description=description,
                    )
                )
            elif tool_name == ExistTools.PRODUCT_SEARCH:
                if self.configuration.file_product_path is None:
                    logger.warning(
                        f"Tool {tool_name} requires file_product_path to be set! But not found, so this tool will be ignored."
                    )
                    continue
                tools.append(
                    load_product_search_tool(
                        file_product_path=self.configuration.file_product_path,
                        description=description,
                    )
                )
            else:
                logger.warning(f"Tool {tool_name} is not supported yet!")
                continue

            return_as_answer_flags.append(return_as_answer)

        kb_agent = Agent(
            role="Assistant",
            goal="Trả lời câu hỏi của người dùng",
            backstory=self.configuration.agent_backstory,
            llm=llm,
            max_execution_time=40,
        )

        kb_task = Task(
            description="Phản hồi tin nhắn của người dùng: {query}.",
            expected_output="Một câu trả lời phù hợp nhất với câu hỏi được đưa ra.",
            agent=kb_agent,
            tools=[
                LlamaIndexTool.from_tool(tool, result_as_answer=return_as_answer_flag)
                for tool, return_as_answer_flag in zip(tools, return_as_answer_flags)
            ],
        )

        self.tools = tools

        return CrewAIAgent(
            agents=[kb_agent],
            tasks=[kb_task],
            manager_llm=llm,
            verbose=True,
            conversation_id=self.configuration.conversation_id,
            use_memory=default_settings.agent_config.use_agent_memory,
        )

    def _init_openai_agent(self):
        model = self.configuration.model
        service = self.configuration.service

        llm = self._init_llama_index_model(service, model)

        tools = []

        self.descriptions = []

        system_prompt = ASSISTANT_SYSTEM_PROMPT.format(
            instruct_prompt=self.configuration.instruct_prompt,
        ).strip("\n")

        for tool_name in self.configuration.tools:
            description = self.configuration.tools[tool_name]["description"]
            return_as_answer = self.configuration.tools[tool_name]["return_as_answer"]

            logger.info(
                {
                    "tool_name": tool_name,
                    "return_as_answer": return_as_answer,
                    "description": description,
                },
            )

            self.descriptions.append(description)

            if tool_name == ExistTools.KNOWLEDGE_BASE_QUERY:
                kb_tool = load_llama_index_kb_tool(
                    setting=default_settings,
                    kb_ids=self.configuration.kb_ids,
                    session_id=self.configuration.session_id,
                    is_contextual_rag=self.configuration.is_contextual_rag,
                    system_prompt=system_prompt,
                    return_direct=return_as_answer,
                )
                tools.append(kb_tool)

            elif tool_name == ExistTools.PRODUCT_SEARCH:
                if self.configuration.file_product_path is None:
                    logger.warning(
                        f"Tool {tool_name} requires file_product_path to be set! But not found, so this tool will be ignored."
                    )
                    continue

                product_search_tool = load_product_search_tool(
                    file_product_path=self.configuration.file_product_path,
                    return_direct=return_as_answer,
                )
                tools.append(product_search_tool)
            else:
                logger.warning(f"Tool {tool_name} is not supported yet!")
                continue

        self.tools = tools

        return OpenAIAgent.from_tools(
            tools=tools,
            llm=llm,
            verbose=True,
            # We use agent_backstory from crewai agent configuration to set system_prompt here
            system_prompt=self.configuration.agent_backstory,
        )

    def _init_langchain_model(self, service, model_id):
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
        logger.info(f"Loading langchain model: {model_id}")

        if service == "openai":
            logger.info(f"Loading OpenAI Model: {model_id}")

            return ChatOpenAI(
                model=model_id,
                temperature=self.configuration.temperature,
            )

        else:
            raise NotImplementedError(
                "The implementation for other types of LLMs are not ready yet!"
            )

    def _init_llama_index_model(self, service: str, model_id: str):
        logger.info(f"Loading llama-index model: {model_id}")

        if service == "openai":
            logger.info(f"Loading OpenAI Model: {model_id}")

            return OpenAI(
                model_id,
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

    @observe()
    async def aon_message(
        self,
        message: str,
        message_history: list[MesssageHistory],
        session_id: str | uuid.UUID,
    ) -> str:
        langfuse_callback_handler.set_trace_params(
            name="aon_message",
            session_id=str(session_id),
        )

        if self.configuration.agent_type == ExistAgentType.CREWAI_AGENT:
            inputs = {
                "query": message,
            }
            response = await self.agent.chat_async(inputs, message_history)

            logger.debug("Use CrewAIAgent")
            logger.debug(f"message: {message}")
            logger.debug(f"response: {response}")
            logger.debug(f"\n{"=" * 100}\n")

            return response

        elif self.configuration.agent_type == ExistAgentType.OPENAI_AGENT:
            logger.debug("Use OpenAIAgent")
            logger.debug(f"message: {message}")

            # Since OpenAIAgent does not support tool with long description yet
            # Use workaround method: https://docs.llamaindex.ai/en/stable/examples/agentopenai_agent_lengthy_tools/#moving-tool-descriptions-to-the-prompt
            tools_description = "\n\n".join(
                [
                    f"Tool Name: {tool.metadata.name}\n"
                    + f"Tool Description: {description} "
                    for tool, description in zip(self.tools, self.descriptions)
                ]
            )

            prompt = f"{tools_description}\n\nMessage: {message}"

            result = await self.agent.achat(prompt)

            response = result.response

            logger.debug(f"response: {response}")
            logger.debug(f"\n{"=" * 100}\n")

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
