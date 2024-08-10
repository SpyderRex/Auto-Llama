"""Functions for counting the number of tokens in a message or string."""
from __future__ import annotations
import nltk
from typing import List
from nltk.tokenize import word_tokenize
from autollama.llm.base import Message

import re

nltk.download("punkt")


def preprocess_text(text: str) -> str:
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text)

    # Replace specific characters or sequences with placeholders
    text = re.sub(r'([^\w\s-])', r' \1 ', text)

    # Separate punctuation from words
    text = re.sub(r'(\w+)([!"#$%&\'()*+,-./:;<=>?@\[\\\]^_`{|}~])', r'\1 \2 ', text)

    # Separate hyphens that are not part of words
    text = re.sub(r'(\s-|-\s)', r' - ', text)

    return text


def count_message_tokens(messages: List[Message]) -> int:
    """
    Returns the number of tokens used by a list of messages.

    Args:
        messages (list): A list of messages, each of which is a dictionary
            containing the role and content of the message.

    Returns:
        int: The number of tokens used by the list of messages.
    """
    tokens_per_message = 4  # every message follows {role/name}\n{content}\n
    tokens_per_name = -1  # if there's a name, the role is omitted

    num_tokens = 0
    for message in messages:
        num_tokens += tokens_per_message
        for key, value in message.items():
            preprocessed_value = preprocess_text(value)
            num_tokens += len(word_tokenize(preprocessed_value))
            if key == "name":
                num_tokens += tokens_per_name
    num_tokens += 3  # every reply is primed with assistant
    return num_tokens


def count_string_tokens(string: str) -> int:
    """
    Returns the number of tokens in a text string.

    Args:
        string (str): The text string.

    Returns:
        int: The number of tokens in the text string.
    """
    preprocessed_string = preprocess_text(string)
    return len(word_tokenize(preprocessed_string))
