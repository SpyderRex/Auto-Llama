"""Configuration class to store the state of bools for different scripts access."""
import os
from typing import List
import yaml
from colorama import Fore

from autollama.singleton import Singleton


class Config(metaclass=Singleton):
    """
    Configuration class to store the state of bools for different scripts access.
    """

    def __init__(self) -> None:
        """Initialize the Config class"""
        self.workspace_path = None
        self.file_logger_path = None

        self.debug_mode = False
        self.continuous_mode = False
        self.continuous_limit = 0
        self.skip_reprompt = False
        self.allow_downloads = False

        self.authorise_key = os.getenv("AUTHORISE_COMMAND_KEY", "y")
        self.exit_key = os.getenv("EXIT_KEY", "n")
        self.ai_settings_file = os.getenv("AI_SETTINGS_FILE", "ai_settings.yaml")
        self.llama_ai_model = "llama3-8b-8192"
        self.token_limit = 8000
        self.embedding_token_limit = int(os.getenv("EMBEDDING_TOKEN_LIMIT", 8191))
        self.browse_chunk_max_length = int(os.getenv("BROWSE_CHUNK_MAX_LENGTH", 3000))

        self.groq_api_key = "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"
        self.temperature = float(os.getenv("TEMPERATURE", "0"))
        self.execute_local_commands = (
            os.getenv("EXECUTE_LOCAL_COMMANDS", "False") == "True"
        )
        self.restrict_to_workspace = (
            os.getenv("RESTRICT_TO_WORKSPACE", "True") == "True"
        )

        self.use_mac_os_tts = False
        self.use_mac_os_tts = os.getenv("USE_MAC_OS_TTS")

        self.chat_messages_enabled = os.getenv("CHAT_MESSAGES_ENABLED") == "True"


        self.github_api_key = os.getenv("GITHUB_API_KEY")
        self.github_username = os.getenv("GITHUB_USERNAME")

        self.google_api_key = os.getenv("GOOGLE_API_KEY")
        self.custom_search_engine_id = os.getenv("CUSTOM_SEARCH_ENGINE_ID")


        

        # Selenium browser settings
        self.selenium_web_browser = os.getenv("USE_WEB_BROWSER", "firefox")
        self.selenium_headless = os.getenv("HEADLESS_BROWSER", "True") == "True"

        # User agent header to use when making HTTP requests
        # Some websites might just completely deny request with an error code if
        # no user agent was found.
        self.user_agent = os.getenv(
            "USER_AGENT",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36"
            " (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36",
        )
        self.memory_index = os.getenv("MEMORY_INDEX", "auto-llama")
        # Note that indexes must be created on db 0 in redis, this is not configurable.

        self.memory_backend = os.getenv("MEMORY_BACKEND", "local")


    def set_continuous_mode(self, value: bool) -> None:
        """Set the continuous mode value."""
        self.continuous_mode = value

    def set_continuous_limit(self, value: int) -> None:
        """Set the continuous limit value."""
        self.continuous_limit = value


    def set_embedding_model(self, value: str) -> None:
        """Set the model to use for creating embeddings."""
        self.embedding_model = value

    def set_embedding_tokenizer(self, value: str) -> None:
        """Set the tokenizer to use when creating embeddings."""
        self.embedding_tokenizer = value

    def set_embedding_token_limit(self, value: int) -> None:
        """Set the token limit for creating embeddings."""
        self.embedding_token_limit = value

    def set_browse_chunk_max_length(self, value: int) -> None:
        """Set the browse_website command chunk max length value."""
        self.browse_chunk_max_length = value

    def set_groq_api_key(self, value: str) -> None:
        """Set the Groq API key value."""
        self.groq_api_key = value

    

    def set_google_api_key(self, value: str) -> None:
        """Set the Google API key value."""
        self.google_api_key = value

    def set_custom_search_engine_id(self, value: str) -> None:
        """Set the custom search engine id value."""
        self.custom_search_engine_id = value

    def set_debug_mode(self, value: bool) -> None:
        """Set the debug mode value."""
        self.debug_mode = value

    def set_temperature(self, value: int) -> None:
        """Set the temperature value."""
        self.temperature = value

    def set_memory_backend(self, name: str) -> None:
        """Set the memory backend name."""
        self.memory_backend = name


def check_groq_api_key() -> None:
    """Check if the Groq API key is set in config.py or as an environment variable."""
    cfg = Config()
    if not cfg.groq_api_key:
        print(
            Fore.RED
            + "Please set your Groq API key in .env or as an environment variable."
            + Fore.RESET
        )
        exit(1)
