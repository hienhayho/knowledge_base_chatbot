import json_repair
from llama_index.llms.openai import OpenAI
from llama_index.core.llms import ChatMessage
from llama_index.core import ChatPromptTemplate

from src.utils import get_formatted_logger
from src.constants import CHAT_AGENT_RESPONSE_PROMPT
from src.settings import default_settings, GlobalSettings

logger = get_formatted_logger(__file__)


def get_default_output_parser():
    return OutputParser(default_settings)


class OutputParser:
    """
    Output parser for the chat assistant. Responsible for parsing the output into json format.
    """

    def __init__(self, settings: GlobalSettings):
        self.settings = settings
        self.llm_output_parser = self._init_llm_output_parser(
            service=self.settings.llm_config.service,
            model_id=self.settings.llm_config.name,
        )

    def _parse_output(self, response: str):
        prompt = ChatPromptTemplate(
            message_templates=[
                ChatMessage(role="system", content=CHAT_AGENT_RESPONSE_PROMPT),
                ChatMessage(
                    role="user",
                    content=(
                        "Here is the content you need to extract info: \n"
                        "------\n"
                        "{content}\n"
                        "------"
                    ),
                ),
            ]
        )

        messages = prompt.format_messages(content=response)

        output = self.llm_output_parser.chat(
            messages, response_format={"type": "json_object"}
        ).message.content

        try:
            result = json_repair.loads(output)
            assert "text" in result, "Missing 'text' key in the output!"
            assert "products" in result, "Missing 'products' key in the output!"
        except Exception as e:
            logger.error(f"Error parsing output: {e}")
            result = {
                "text": "Parsing error!",
                "products": [],
            }

        return result

    def _init_llm_output_parser(self, service, model_id):
        """
        Initialize the LLM output parser for the chat assistant.

        Args:
            service (str): Service name indicating the type of model to load.
            model_id (str): Identifier of the model to load from HuggingFace's model hub.
        """
        logger.info(f"Loading LLM Output Parser: {model_id}")

        if service == "openai":
            return OpenAI(
                model=model_id,
            )
        else:
            raise NotImplementedError(
                "The implementation for other types of LLM output parsers are not ready yet!"
            )
