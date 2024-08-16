"""Functions for counting the number of tokens in a message or string."""
from __future__ import annotations

from typing import List
import re

from autollama.llm.base import Message
from autollama.logs import logger


def simple_tokenizer(text: str) -> List[str]:
    """
    Tokenizes a string into words based on whitespace and basic punctuation.
    
    Args:
        text (str): The input text to tokenize.

    Returns:
        List[str]: A list of tokens.
    """
    # Simple tokenizer: split by whitespace and punctuation
    tokens = re.findall(r'\w+|\S', text)
    return tokens


def count_message_tokens(
    messages: List[Message], encoding_name: str = "custom"
) -> int:
    """
    Returns the number of tokens used by a list of messages.

    Args:
        messages (list): A list of messages, each of which is a dictionary
            containing the role and content of the message.
        encoding_name (str): This parameter is retained for compatibility, but is not used.

    Returns:
        int: The number of tokens used by the list of messages.
    """
    tokens_per_message = 4  # Adjust this based on the expected format of your messages
    tokens_per_name = -1  # Adjust based on the presence of a name field

    num_tokens = 0
    for message in messages:
        num_tokens += tokens_per_message
        for key, value in message.items():
            tokens = simple_tokenizer(value)
            num_tokens += len(tokens)
            if key == "name":
                num_tokens += tokens_per_name
    num_tokens += 3  # Adjust this based on the format of your replies
    return num_tokens


def count_string_tokens(string: str, encoding_name: str = "custom") -> int:
    """
    Returns the number of tokens in a text string.

    Args:
        string (str): The text string.
        encoding_name (str): This parameter is retained for compatibility, but is not used.

    Returns:
        int: The number of tokens in the text string.
    """
    tokens = simple_tokenizer(string)
    return len(tokens)
