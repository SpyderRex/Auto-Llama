from __future__ import annotations

import functools
import time
from itertools import islice
from typing import List, Optional

import numpy as np
import spacy
from colorama import Fore, Style

from autollama.config import Config
from autollama.llm.api_manager import ApiManager
from autollama.llm.base import Message
from autollama.logs import logger


def retry_api(
    num_retries: int = 10,
    backoff_base: float = 2.0,
    warn_user: bool = True,
):
    """Retry an API call.

    Args:
        num_retries int: Number of retries. Defaults to 10.
        backoff_base float: Base for exponential backoff. Defaults to 2.
        warn_user bool: Whether to warn the user. Defaults to True.
    """
    retry_limit_msg = f"{Fore.RED}Error: " f"Reached rate limit, passing...{Fore.RESET}"
    api_key_error_msg = (
        f"Please double check that you have setup a valid API Account."
    )
    backoff_msg = (
        f"{Fore.RED}Error: API Bad gateway. Waiting {{backoff}} seconds...{Fore.RESET}"
    )

    def _wrapper(func):
        @functools.wraps(func)
        def _wrapped(*args, **kwargs):
            user_warned = not warn_user
            num_attempts = num_retries + 1  # +1 for the first attempt
            for attempt in range(1, num_attempts + 1):
                try:
                    return func(*args, **kwargs)

                except Exception as e:
                    if attempt == num_attempts:
                        raise
                    logger.debug(retry_limit_msg)
                    if not user_warned:
                        logger.double_check(api_key_error_msg)
                        user_warned = True

                backoff = backoff_base ** (attempt + 2)
                logger.debug(backoff_msg.format(backoff=backoff))
                time.sleep(backoff)

        return _wrapped

    return _wrapper


def call_ai_function(
    function: str, args: list, description: str, model: str | None = None
) -> str:
    """Call an AI function.

    This is a magic function that can do anything with no-code.

    Args:
        function (str): The function to call.
        args (list): The arguments to pass to the function.
        description (str): The description of the function.
        model (str, optional): The model to use. Defaults to None.

    Returns:
        str: The response from the function.
    """
    cfg = Config()
    if model is None:
        model = cfg.llm_model
    # For each arg, if any are None, convert to "None":
    args = [str(arg) if arg is not None else "None" for arg in args]
    # parse args to comma-separated string
    args: str = ", ".join(args)
    messages: List[Message] = [
        {
            "role": "system",
            "content": f"You are now the following python function: ```# {description}"
            f"\n{function}```\n\nOnly respond with your `return` value.",
        },
        {"role": "user", "content": args},
    ]

    return create_chat_completion(messages=messages, temperature=0)


# Overly simple abstraction until we create something better
# simple retry mechanism when getting a rate error or a bad gateway
def create_chat_completion(
    messages: List[Message],  # type: ignore
    model: Optional[str] = None,
    temperature: float = None,
    max_tokens: Optional[int] = None,
) -> str:
    """Create a chat completion using the configured API.

    Args:
        messages (List[Message]): The messages to send to the chat completion.
        model (str, optional): The model to use. Defaults to None.
        temperature (float, optional): The temperature to use. Defaults to 0.9.
        max_tokens (int, optional): The max tokens to use. Defaults to None.

    Returns:
        str: The response from the chat completion.
    """
    cfg = Config()
    if temperature is None:
        temperature = cfg.temperature

    num_retries = 10
    warned_user = False
    logger.debug(
        f"{Fore.GREEN}Creating chat completion with model {model}, temperature {temperature}, max_tokens {max_tokens}{Fore.RESET}"
    )
    api_manager = ApiManager()
    response = None
    for attempt in range(num_retries):
        backoff = 2 ** (attempt + 2)
        try:
            response = api_manager.create_chat_completion(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            break
        except Exception as e:
            logger.debug(
                f"{Fore.RED}Error: ", f"API error occurred, passing...{Fore.RESET}"
            )
            if not warned_user:
                logger.double_check(
                    f"Please double check your API configuration."
                )
                warned_user = True
        logger.debug(
            f"{Fore.RED}Error: ",
            f"API Bad gateway. Waiting {backoff} seconds...{Fore.RESET}",
        )
        time.sleep(backoff)
    if response is None:
        logger.typewriter_log(
            "FAILED TO GET RESPONSE",
            Fore.RED,
            "Auto-Llama has failed to get a response from the configured API service. "
            + f"Try running Auto-Llama again, and if the problem persists, try running it with `{Fore.CYAN}--debug{Fore.RESET}`.",
        )
        logger.double_check()
        if cfg.debug_mode:
            raise RuntimeError(f"Failed to get response after {num_retries} retries")
        else:
            quit(1)
    resp = response.choices[0].message.content
    return resp


def batched(iterable, n):
    """Batch data into tuples of length n. The last batch may be shorter."""
    # batched('ABCDEFG', 3) --> ABC DEF G
    if n < 1:
        raise ValueError("n must be at least one")
    it = iter(iterable)
    while batch := tuple(islice(it, n)):
        yield batch


def chunked_tokens(text, tokenizer_name, chunk_length):
    """Chunk tokens based on length."""
    tokenizer = spacy.blank(tokenizer_name)
    tokens = tokenizer(text)
    chunks_iterator = batched(tokens, chunk_length)
    yield from chunks_iterator


def get_spacy_embedding(text: str) -> List[float]:
    """Get an embedding using Spacy.

    Args:
        text (str): The text to embed.

    Returns:
        List[float]: The embedding.
    """
    cfg = Config()
    model = cfg.embedding_model
    text = text.replace("\n", " ")

    embedding = create_embedding(text, model=model)
    return embedding


@retry_api()
def create_embedding(
    text: str,
    model: Optional[str] = None,
    **kwargs,
) -> List[float]:
    """Create an embedding using Spacy.

    Args:
        text (str): The text to embed.
        model (str, optional): The model to use. Defaults to None.

    Returns:
        List[float]: The embedding.
    """
    cfg = Config()
    nlp = spacy.load(model if model else cfg.embedding_model)
    doc = nlp(text)
    embedding = doc.vector.tolist()
    return embedding 
