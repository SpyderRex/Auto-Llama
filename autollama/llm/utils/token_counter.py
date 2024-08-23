"""Functions for counting the number of tokens in a message or string."""
from __future__ import annotations

from typing import List

from autollama.llm.base import Message
from autollama.logs import logger
from autollama.config import Config

cfg = Config()

def count_message_tokens(
    messages: List[Message], model: str = cfg.llm_model
) -> int:
    """
    Returns the number of tokens used by a list of messages.

    Args:
        messages (list): A list of messages, each of which is a dictionary
            containing the role and content of the message.
        model (str): The name of the model to use for tokenization.
            Defaults to the model defined in the config file.

    Returns:
        int: The number of tokens used by the list of messages.
    """
    tokens_per_message = 4  # every message follows {role/name}\n{content}\n
    tokens_per_name = -1  # if there's a name, the role is omitted

    num_tokens = 0
    for message in messages:
        num_tokens += tokens_per_message
        for key, value in message.raw().items():
            num_tokens += len(value.split())  # Simple token counting based on words
            if key == "name":
                num_tokens += tokens_per_name
    num_tokens += 3  # every reply is primed with assistant
    return num_tokens


def count_string_tokens(string: str, model_name: str = cfg.llm_model) -> int:
    """
    Returns the number of tokens in a text string.

    Args:
        string (str): The text string.
        model_name (str): The name of the encoding to use. Defaults to the model defined in the config file.

    Returns:
        int: The number of tokens in the text string.
    """
    return len(string.split())  # Simple token counting based on words
