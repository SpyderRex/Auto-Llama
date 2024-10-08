"""The application entry point.  Can be invoked by a CLI or any other front end application."""
import logging
import sys
from pathlib import Path

from colorama import Fore, Style

from autollama.agent import Agent
from autollama.commands.command import CommandRegistry
from autollama.config import Config, check_groq_api_key
from autollama.configurator import create_config
from autollama.logs import logger
from autollama.memory.vector import get_memory
from autollama.prompts.prompt import DEFAULT_TRIGGERING_PROMPT, construct_main_ai_config
from autollama.utils import (
    markdown_to_ansi_style,
)
from autollama.workspace import Workspace

COMMAND_CATEGORIES = [
    "autollama.commands.analyze_code",
    "autollama.commands.audio_text",
    "autollama.commands.execute_code",
    "autollama.commands.file_operations",
    "autollama.commands.git_operations",
    "autollama.commands.google_search",
    "autollama.commands.image_gen",
    "autollama.commands.improve_code",
    "autollama.commands.web_selenium",
    "autollama.commands.write_tests",
    "autollama.app",
    "autollama.commands.task_statuses",
]


def run_auto_llama(
    continuous: bool,
    continuous_limit: int,
    ai_settings: str,
    prompt_settings: str,
    skip_reprompt: bool,
    speak: bool,
    debug: bool,
    memory_type: str,
    browser_name: str,
    allow_downloads: bool,
    workspace_directory: str,
):
    # Configure logging before we do anything else.
    logger.set_level(logging.DEBUG if debug else logging.INFO)
    logger.speak_mode = speak

    cfg = Config()
    # TODO: fill in llm values here
    check_groq_api_key()

    create_config(
        cfg,
        continuous,
        continuous_limit,
        ai_settings,
        prompt_settings,
        skip_reprompt,
        speak,
        debug,
        memory_type,
        browser_name,
        allow_downloads,
    )

    if cfg.continuous_mode:
    
        if sys.version_info < (3, 10):
            logger.typewriter_log(
                "WARNING: ",
                Fore.RED,
                "You are running on an older version of Python. "
                "Some people have observed problems with certain "
                "parts of Auto-Llama with this version. "
                "Please consider upgrading to Python 3.10 or higher.",
            )

    # TODO: have this directory live outside the repository (e.g. in a user's
    #   home directory) and have it come in as a command line argument or part of
    #   the env file.
    if workspace_directory is None:
        workspace_directory = Path(__file__).parent / "auto_llama_workspace"
    else:
        workspace_directory = Path(workspace_directory)
    # TODO: pass in the ai_settings file and the env file and have them cloned into
    #   the workspace directory so we can bind them to the agent.
    workspace_directory = Workspace.make_workspace(workspace_directory)
    cfg.workspace_path = str(workspace_directory)

    # HACK: doing this here to collect some globals that depend on the workspace.
    file_logger_path = workspace_directory / "file_logger.txt"
    if not file_logger_path.exists():
        with file_logger_path.open(mode="w", encoding="utf-8") as f:
            f.write("File Operation Logger ")

    cfg.file_logger_path = str(file_logger_path)

    # Create a CommandRegistry instance and scan default folder
    command_registry = CommandRegistry()

    logger.debug(
        f"The following command categories are disabled: {cfg.disabled_command_categories}"
    )
    enabled_command_categories = [
        x for x in COMMAND_CATEGORIES if x not in cfg.disabled_command_categories
    ]

    logger.debug(
        f"The following command categories are enabled: {enabled_command_categories}"
    )

    for command_category in enabled_command_categories:
        command_registry.import_commands(command_category)

    ai_name = ""
    ai_config = construct_main_ai_config()
    ai_config.command_registry = command_registry
    if ai_config.ai_name:
        ai_name = ai_config.ai_name
    # print(prompt)
    # Initialize variables
    next_action_count = 0

    # Initialize memory and make sure it is empty.
    # this is particularly important for indexing and referencing pinecone memory
    memory = get_memory(cfg, init=True)
    logger.typewriter_log(
        "Using memory of type:", Fore.GREEN, f"{memory.__class__.__name__}"
    )
    logger.typewriter_log("Using Browser:", Fore.GREEN, cfg.selenium_web_browser)
    system_prompt = ai_config.construct_full_prompt()
    if cfg.debug_mode:
        logger.typewriter_log("Prompt:", Fore.GREEN, system_prompt)

    agent = Agent(
        ai_name=ai_name,
        memory=memory,
        next_action_count=next_action_count,
        command_registry=command_registry,
        config=ai_config,
        system_prompt=system_prompt,
        triggering_prompt=DEFAULT_TRIGGERING_PROMPT,
        workspace_directory=workspace_directory,
    )
    agent.start_interaction_loop()
