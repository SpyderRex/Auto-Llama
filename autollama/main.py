"""The application entry point. Can be invoked by a CLI or any other front-end application."""
import logging
from pathlib import Path

from colorama import Fore

from autollama.agent.agent import Agent
from autollama.commands.command import CommandRegistry
from autollama.config import Config, check_groq_api_key
from autollama.configurator import create_config
from autollama.logs import logger
from autollama.memory import get_memory
from autollama.prompts.prompt import DEFAULT_TRIGGERING_PROMPT, construct_main_ai_config
from autollama.workspace import Workspace

def run_auto_llama(
    continuous: bool,
    continuous_limit: int,
    ai_settings: str,
    skip_reprompt: bool,
    debug: bool,
    memory_type: str,
    browser_name: str,
    allow_downloads: bool,
    workspace_directory: str = None,
):
    # Configure logging
    logger.set_level(logging.DEBUG if debug else logging.INFO)
    
    # Initial debug output for troubleshooting
    logger.debug(f"Running with parameters: continuous={continuous}, "
                 f"continuous_limit={continuous_limit}, ai_settings='{ai_settings}', "
                 f"skip_reprompt={skip_reprompt}, debug={debug}, "
                 f"memory_type='{memory_type}', browser_name='{browser_name}', "
                 f"allow_downloads={allow_downloads}, workspace_directory='{workspace_directory}'")

    cfg = Config()
    check_groq_api_key()

    create_config(
        continuous,
        continuous_limit,
        ai_settings,
        skip_reprompt,
        debug,
        memory_type,
        browser_name,
        allow_downloads,
        workspace_directory,
    )

    workspace_directory = Path(workspace_directory or Path(__file__).parent / "auto_llama_workspace")
    logger.debug(f"Resolved workspace directory: {workspace_directory}")

    workspace_directory = Workspace.make_workspace(workspace_directory)
    cfg.workspace_path = str(workspace_directory)

    # Debugging for workspace path
    logger.info(f"Workspace path set to: {cfg.workspace_path}")

    # Ensure the file logger is properly set up
    file_logger_path = workspace_directory / "file_logger.txt"
    if not file_logger_path.exists():
        logger.debug(f"Creating file logger at: {file_logger_path}")
        file_logger_path.write_text("File Operation Logger\n", encoding="utf-8")
    else:
        logger.debug(f"File logger already exists at: {file_logger_path}")

    cfg.file_logger_path = str(file_logger_path)
    
    # Test file writing permissions by writing a test file
    test_file_path = workspace_directory / "test_write.txt"
    try:
        test_file_path.write_text("Test write to verify permissions.\n", encoding="utf-8")
        logger.info("Test file written successfully.")
    except Exception as e:
        logger.error(f"Failed to write test file. Error: {e}")
        return

    command_registry = CommandRegistry()
    command_modules = [
        "autollama.commands.analyze_code",
        "autollama.commands.execute_code",
        "autollama.commands.file_operations",
        "autollama.commands.git_operations",
        "autollama.commands.google_search",
        "autollama.commands.improve_code",
        "autollama.commands.web_selenium",
        "autollama.commands.write_tests",
        "autollama.app",
        "autollama.commands.task_statuses",
    ]
    
    for module in command_modules:
        logger.debug(f"Importing commands from module: {module}")
        command_registry.import_commands(module)

    ai_config = construct_main_ai_config()
    ai_config.command_registry = command_registry

    memory = get_memory(cfg, init=True)
    logger.typewriter_log("Using memory of type:", Fore.GREEN, f"{memory.__class__.__name__}")
    logger.typewriter_log("Using Browser:", Fore.GREEN, cfg.selenium_web_browser)

    if cfg.debug_mode:
        logger.typewriter_log("Prompt:", Fore.GREEN, ai_config.construct_full_prompt())

    agent = Agent(
        ai_name="AutoLlama",
        memory=memory,
        full_message_history=[],
        next_action_count=0,
        command_registry=command_registry,
        config=ai_config,
        system_prompt=ai_config.construct_full_prompt(),
        triggering_prompt=DEFAULT_TRIGGERING_PROMPT,
        workspace_directory=workspace_directory,
    )

    # Start the interaction loop
    logger.info("Starting the interaction loop...")
    agent.start_interaction_loop()
