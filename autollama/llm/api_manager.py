from __future__ import annotations

from typing import List, Optional

from groq import Groq

from autollama.config import Config
from autollama.llm.base import MessageDict
from autollama.llm.modelsinfo import COSTS
from autollama.logs import logger
from autollama.singleton import Singleton


class ApiManager(metaclass=Singleton):
    def __init__(self):
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0
        self.total_cost = 0
        self.models: Optional[list[Model]] = None

    def reset(self):
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0
        self.total_cost = 0
        self.models = None

    def create_chat_completion(
        self,
        messages: list[MessageDict],
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
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        if not hasattr(response, "error"):
            logger.debug(f"Response: {response}")
            prompt_tokens = response.usage.prompt_tokens
            completion_tokens = response.usage.completion_tokens
            self.update_cost(prompt_tokens, completion_tokens, model)
        return response

    def update_cost(self, prompt_tokens, completion_tokens, model: str):
        """
        Update the total cost, prompt tokens, and completion tokens.

        Args:
        prompt_tokens (int): The number of tokens used in the prompt.
        completion_tokens (int): The number of tokens used in the completion.
        model (str): The model used for the API call.
        """
        model = model[:-3] if model.endswith("-v2") else model

        self.total_prompt_tokens += prompt_tokens
        self.total_completion_tokens += completion_tokens
        self.total_cost += (
            prompt_tokens * COSTS[model]["prompt"]
            + completion_tokens * COSTS[model]["completion"]
        ) / 1000
        logger.debug(f"Total running cost: ${self.total_cost:.3f}")


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

    def get_total_cost(self):
        """
        Get the total cost of API calls.

        Returns:
        float: The total cost of API calls.
        """
        return self.total_cost


    def get_models(self) -> List[Model]:
        """
        Get list of available Llama models.

        Returns:
        list: List of available Llama models.

        """
        if self.models is None:
            all_models = ["llama3-8b-8192"]
        return self.models
