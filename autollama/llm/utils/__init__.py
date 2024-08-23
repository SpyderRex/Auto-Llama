from __future__ import annotations

import functools
import time
from typing import List, Literal, Optional
from unittest.mock import patch

from colorama import Fore, Style
from groq import APIError, RateLimitError
from groq import Groq

from autollama.config import Config
from autollama.logs import logger

from ..api_manager import ApiManager
from ..base import ChatSequence, Message
from .token_counter import *


def retry_groq_api(
    num_retries: int = 10,
    backoff_base: float = 2.0,
    warn_user: bool = True,
):
    """Retry an Groq API call.

    Args:
        num_retries int: Number of retries. Defaults to 10.
        backoff_base float: Base for exponential backoff. Defaults to 2.
        warn_user bool: Whether to warn the user. Defaults to True.
    """
    retry_limit_msg = f"{Fore.RED}Error: " f"Reached rate limit, passing...{Fore.RESET}"
    api_key_error_msg = (
        f"Please double check that you have setup a "
        f"{Fore.CYAN + Style.BRIGHT}PAID{Style.RESET_ALL} Groq API Account."
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

                except RateLimitError:
                    if attempt == num_attempts:
                        raise

                    logger.debug(retry_limit_msg)
                    if not user_warned:
                        logger.double_check(api_key_error_msg)
                        user_warned = True

                except APIError as e:
                    if (e.message not in [502, 429]) or (attempt == num_attempts):
                        raise

                backoff = backoff_base ** (attempt + 2)
                logger.debug(backoff_msg.format(backoff=backoff))
                time.sleep(backoff)

        return _wrapped

    return _wrapper


def call_ai_function(
    function: str,
    args: list,
    description: str,
    model: str | None = None,
    config: Config = None,
) -> str:
    """Call an AI function

    This is a magic function that can do anything with no-code.

    Args:
        function (str): The function to call
        args (list): The arguments to pass to the function
        description (str): The description of the function
        model (str, optional): The model to use. Defaults to None.

    Returns:
        str: The response from the function
    """
    if model is None:
        model = config.llm_model
    # For each arg, if any are None, convert to "None":
    args = [str(arg) if arg is not None else "None" for arg in args]
    # parse args to comma separated string
    arg_str: str = ", ".join(args)

    prompt = ChatSequence.for_model(
        model,
        [
            Message(
                "system",
                f"You are now the following python function: ```# {description}"
                f"\n{function}```\n\nOnly respond with your `return` value.",
            ),
            Message("user", arg_str),
        ],
    )
    return create_chat_completion(prompt=prompt, temperature=0)


@retry_groq_api()
def create_text_completion(
    prompt: str,
    model: Optional[str],
    temperature: Optional[float],
    max_output_tokens: Optional[int],
) -> str:
    cfg = Config()
    client = Groq(api_key=cfg.groq_api_key)
    if model is None:
        model = cfg.llm_model
    if temperature is None:
        temperature = cfg.temperature

    kwargs = {"model": model}

    response = client.chat.completions.create(
        **kwargs,
        prompt=prompt,
        temperature=temperature,
        max_tokens=max_output_tokens,
    )
    return response.choices[0].message


# Overly simple abstraction until we create something better
# simple retry mechanism when getting a rate error or a bad gateway
@retry_groq_api()
def create_chat_completion(
    prompt: ChatSequence,
    model: Optional[str] = None,
    temperature: float = None,
    max_tokens: Optional[int] = None,
) -> str:
    """Create a chat completion using the Groq API

    Args:
        messages (List[Message]): The messages to send to the chat completion
        model (str, optional): The model to use. Defaults to None.
        temperature (float, optional): The temperature to use. Defaults to 0.9.
        max_tokens (int, optional): The max tokens to use. Defaults to None.

    Returns:
        str: The response from the chat completion
    """
    cfg = Config()
    if model is None:
        model = prompt.model.name
    if temperature is None:
        temperature = cfg.temperature

    logger.debug(
        f"{Fore.GREEN}Creating chat completion with model {model}, temperature {temperature}, max_tokens {max_tokens}{Fore.RESET}"
    )
  
    api_manager = ApiManager()
    response = None

    kwargs = {"model": model}

    response = api_manager.create_chat_completion(
        **kwargs,
        messages=prompt.raw(),
        temperature=temperature,
        max_tokens=max_tokens,
    )

    resp = response.choices[0].message.content
    return resp


def check_model(
    model_name: str, model_type: Literal["llm_model"]
) -> str:
    """Check if model is available for use."""
    api_manager = ApiManager()
    models = api_manager.get_models()

    if any(model_name in m["id"] for m in models):
        return model_name

    logger.typewriter_log(
        "WARNING: ",
        Fore.YELLOW,
        f"You do not have access to {model_name}."
    )
    return "Bye."
