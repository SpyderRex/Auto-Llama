from __future__ import annotations
import os
import functools
import time
from itertools import islice
from typing import List, Optional, Iterator

import nltk
from colorama import Fore, Style
from groq import Groq

from autollama.config import Config
from autollama.llm.api_manager import ApiManager
from autollama.llm.base import Message
from autollama.logs import logger

cfg = Config()

def retry_api(
    num_retries: int = 10,
    backoff_base: float = 2.0,
    warn_user: bool = True,
):
    """Retry an API call with exponential backoff.

    Args:
        num_retries int: Number of retries. Defaults to 10.
        backoff_base float: Base for exponential backoff. Defaults to 2.
        warn_user bool: Whether to warn the user. Defaults to True.
    """
    retry_limit_msg = f"{Fore.RED}Error: " f"Reached rate limit, passing...{Fore.RESET}"
    backoff_msg = f"{Fore.RED}Error: API Bad gateway. Waiting {{backoff}} seconds...{Fore.RESET}"

    def _wrapper(func):
        @functools.wraps(func)
        def _wrapped(*args, **kwargs):
            user_warned = not warn_user
            num_attempts = num_retries + 1  # +1 for the first attempt
            for attempt in range(1, num_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    print(e)
                    if attempt == num_attempts:
                        raise

                    logger.debug(retry_limit_msg)
                    if not user_warned:
                        logger.double_check("Please double check your Groq API setup.")
                        user_warned = True

                backoff = backoff_base ** (attempt + 2)
                logger.debug(backoff_msg.format(backoff=backoff))
                time.sleep(backoff)

        return _wrapped

    return _wrapper


def call_ai_function(
    function: str, args: list, description: str, model: str | None = None
) -> str:
    """Call an AI function using Groq's API.

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
        model = cfg.llama_ai_model
    # Convert any None arguments to "None" as a string
    args = [str(arg) if arg is not None else "None" for arg in args]
    # Parse args to comma-separated string
    args: str = ", ".join(args)
    messages: List[Message] = [
        {
            "role": "system",
            "content": f"You are now the following python function: ```# {description}"
            f"\n{function}```\n\nOnly respond with your `return` value.",
        },
        {"role": "user", "content": args},
    ]

    return create_chat_completion(model=model, messages=messages, temperature=0)


def create_chat_completion(
    messages: List[Message],  # type: ignore
    model: cfg.llama_ai_model,
    temperature: float = None,
    max_tokens: Optional[int] = None,
) -> str:
    """Create a chat completion using the Groq API.

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
    
    api_key = cfg.groq_api_key
    client = Groq(api_key=api_key)
    response = None
    for attempt in range(num_retries):
        backoff = 2 ** (attempt + 2)
        try:
            response = client.chat.completions.create(
                messages=messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            break  # Exit loop if successful
        except Exception as e:
            print(e)
            logger.debug(f"{Fore.RED}Error: Reached rate limit, passing...{Fore.RESET}")
            if not warned_user:
                logger.double_check("Please double check your Groq API setup.")
                warned_user = True
        logger.debug(f"{Fore.RED}API Bad gateway. Waiting {backoff} seconds...{Fore.RESET}")
        time.sleep(backoff)
    
    if response is None:
        logger.typewriter_log(
            "FAILED TO GET RESPONSE FROM GROQ",
            Fore.RED,
            "Auto-Llama has failed to get a response from Groq's services. "
            + f"Try running Auto-Llama again, and if the problem persists, try running it with `{Fore.CYAN}--debug{Fore.RESET}`.",
        )
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


def chunked_tokens(text: str, tokenizer_name: str, chunk_length: int) -> Iterator[List[str]]:
    """
    Returns an iterator of tokenized chunks from a text.

    Args:
        text (str): The input text.
        tokenizer_name (str): The name of the tokenizer to use.
        chunk_length (int): The maximum length of each chunk.

    Returns:
        Iterator[List[str]]: An iterator of lists of tokens, each with a maximum length of `chunk_length`.
    """
    tokenizer = nltk.tokenize.RegexpTokenizer(r'\w+')
    tokens = tokenizer.tokenize(text)
    chunks_iterator = batched(tokens, chunk_length)
    yield from chunks_iterator

def batched(tokens: List[str], batch_size: int) -> Iterator[List[str]]:
    """
    Returns an iterator of batches of tokens from a list.

    Args:
        tokens (List[str]): A list of tokens.
        batch_size (int): The maximum number of tokens per batch.

    Returns:
        Iterator[List[str]]: An iterator of lists of tokens, each with a maximum length of `batch_size`.
    """
    for i in range(0, len(tokens), batch_size):
        yield tokens[i:i+batch_size]
