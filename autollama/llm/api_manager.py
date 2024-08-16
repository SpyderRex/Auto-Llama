from __future__ import annotations

from groq import Groq

from autollama.config import Config
from autollama.logs import logger
from autollama.singleton import Singleton

class ApiManager(metaclass=Singleton):
    def __init__(self):
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0

    def reset(self):
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0

    def create_chat_completion(
        self,
        messages: list,  # type: ignore
        model: str | None = None,
        temperature: float = None,
        max_tokens: int | None = None,
    ) -> str:
        """
        Create a chat completion and update the cost.
        Args:
        messages (list): The list of messages to send to the API.
        model (str): The model to use for the API call.
        temperature (float): The temperature to use for the API call.
        max_tokens (int): The maximum number of tokens for the API call.
        Returns:
        str: The AI's response.
        """
        cfg = Config()
        client = Groq(api_key=cfg.groq_api_key)
        if temperature is None:
            temperature = cfg.temperature

        response = client.chat.completions.create(
            model=cfg.llm_model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        logger.debug(f"Response: {response}")
        prompt_tokens = response.usage.prompt_tokens
        completion_tokens = response.usage.completion_tokens

        return response


    def get_total_prompt_tokens(self):
        """
        Get the total number of prompt tokens.

        Returns:
        int: The total number of prompt tokens.
        """
        return self.total_prompt_tokens

    def get_total_completion_tokens(self):
        """
        Get the total number of completion tokens.

        Returns:
        int: The total number of completion tokens.
        """
        return self.total_completion_tokens
