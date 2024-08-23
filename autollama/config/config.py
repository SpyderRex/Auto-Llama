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
        self.workspace_path: str = None
        self.file_logger_path: str = None

        self.debug_mode = False
        self.continuous_mode = False
        self.continuous_limit = 0
        self.speak_mode = False
        self.skip_reprompt = False
        self.allow_downloads = False

        self.authorise_key = os.getenv("AUTHORISE_COMMAND_KEY", "y")
        self.exit_key = os.getenv("EXIT_KEY", "n")
        self.plain_output = os.getenv("PLAIN_OUTPUT", "False") == "True"

        disabled_command_categories = os.getenv("DISABLED_COMMAND_CATEGORIES")
        if disabled_command_categories:
            self.disabled_command_categories = disabled_command_categories.split(",")
        else:
            self.disabled_command_categories = []

        deny_commands = os.getenv("DENY_COMMANDS")
        if deny_commands:
            self.deny_commands = deny_commands.split(",")
        else:
            self.deny_commands = []

        allow_commands = os.getenv("ALLOW_COMMANDS")
        if allow_commands:
            self.allow_commands = allow_commands.split(",")
        else:
            self.allow_commands = []

        self.ai_settings_file = os.getenv("AI_SETTINGS_FILE", "ai_settings.yaml")
        self.prompt_settings_file = os.getenv(
            "PROMPT_SETTINGS_FILE", "prompt_settings.yaml"
        )
        self.llm_model = os.getenv("LLM_MODEL", "llama3-8b-8192")
        self.token_limit = int(os.getenv("TOKEN_LIMIT", 8000))
        self.embedding_model = os.getenv("EMBEDDING_MODEL", "en_core_web_md")
        self.browse_spacy_language_model = os.getenv(
            "BROWSE_SPACY_LANGUAGE_MODEL", "en_core_web_sm"
        )

        self.groq_api_key = os.getenv("GROQ_API_KEY")
        self.temperature = float(os.getenv("TEMPERATURE", "0"))
        self.execute_local_commands = (
            os.getenv("EXECUTE_LOCAL_COMMANDS", "False") == "True"
        )
        self.restrict_to_workspace = (
            os.getenv("RESTRICT_TO_WORKSPACE", "True") == "True"
        )

        self.elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY")
        self.elevenlabs_voice_1_id = os.getenv("ELEVENLABS_VOICE_1_ID")
        self.elevenlabs_voice_2_id = os.getenv("ELEVENLABS_VOICE_2_ID")

        self.use_mac_os_tts = False
        self.use_mac_os_tts = os.getenv("USE_MAC_OS_TTS")

        self.chat_messages_enabled = os.getenv("CHAT_MESSAGES_ENABLED") == "True"

        self.use_brian_tts = False
        self.use_brian_tts = os.getenv("USE_BRIAN_TTS")

        self.github_api_key = os.getenv("GITHUB_API_KEY")
        self.github_username = os.getenv("GITHUB_USERNAME")

        self.google_api_key = os.getenv("GOOGLE_API_KEY")
        self.custom_search_engine_id = os.getenv("CUSTOM_SEARCH_ENGINE_ID")

        self.image_provider = os.getenv("IMAGE_PROVIDER")
        self.image_size = int(os.getenv("IMAGE_SIZE", 256))
        self.huggingface_api_token = os.getenv("HUGGINGFACE_API_TOKEN")
        self.huggingface_image_model = os.getenv(
            "HUGGINGFACE_IMAGE_MODEL", "CompVis/stable-diffusion-v1-4"
        )
        self.huggingface_audio_to_text_model = os.getenv(
            "HUGGINGFACE_AUDIO_TO_TEXT_MODEL"
        )
        self.sd_webui_url = os.getenv("SD_WEBUI_URL", "http://localhost:7860")
        self.sd_webui_auth = os.getenv("SD_WEBUI_AUTH")

        # Selenium browser settings
        self.selenium_web_browser = os.getenv("USE_WEB_BROWSER", "chrome")
        self.selenium_headless = os.getenv("HEADLESS_BROWSER", "True") == "True"

        # User agent header to use when making HTTP requests
        # Some websites might just completely deny request with an error code if
        # no user agent was found.
        self.user_agent = os.getenv(
            "USER_AGENT",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36"
            " (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36",
        )

        self.memory_backend = os.getenv("MEMORY_BACKEND", "json_file")
        self.memory_index = os.getenv("MEMORY_INDEX", "auto-llama-memory")

        self.redis_host = os.getenv("REDIS_HOST", "localhost")
        self.redis_port = int(os.getenv("REDIS_PORT", "6379"))
        self.redis_password = os.getenv("REDIS_PASSWORD", "")
        self.wipe_redis_on_start = os.getenv("WIPE_REDIS_ON_START", "True") == "True"


    def set_continuous_mode(self, value: bool) -> None:
        """Set the continuous mode value."""
        self.continuous_mode = value

    def set_continuous_limit(self, value: int) -> None:
        """Set the continuous limit value."""
        self.continuous_limit = value

    def set_speak_mode(self, value: bool) -> None:
        """Set the speak mode value."""
        self.speak_mode = value

    def set_llm_model(self, value: str) -> None:
        """Set the LLM model value."""
        self.llm_model = value

    def set_token_limit(self, value: int) -> None:
        """Set the fast limit value."""
        self.token_limit = value

    def set_embedding_model(self, value: str) -> None:
        """Set the model to use for creating embeddings."""
        self.embedding_model = value

    def set_groq_api_key(self, value: str) -> None:
        """Set the Groq API key value."""
        self.groq_api_key = value

    def set_elevenlabs_api_key(self, value: str) -> None:
        """Set the ElevenLabs API key value."""
        self.elevenlabs_api_key = value

    def set_elevenlabs_voice_1_id(self, value: str) -> None:
        """Set the ElevenLabs Voice 1 ID value."""
        self.elevenlabs_voice_1_id = value

    def set_elevenlabs_voice_2_id(self, value: str) -> None:
        """Set the ElevenLabs Voice 2 ID value."""
        self.elevenlabs_voice_2_id = value

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
