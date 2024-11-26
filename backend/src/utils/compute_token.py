import tiktoken
from .logger import get_formatted_logger


logger = get_formatted_logger(__file__)


def openai_compute_token(
    prompt: str,
    model: str,
) -> int:
    """
    Compute the number of tokens from prompt for a given model from OpenAI

    Args:
        prompt (str): The prompt to compute the number of tokens from
        model (str): The model to use for tokenization

    Returns:
        int: The number of tokens in the prompt
    """
    encoding = tiktoken.encoding_for_model(model)
    return len(encoding.encode(prompt))
