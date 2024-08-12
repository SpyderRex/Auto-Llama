"""Configurator module."""
import click
from colorama import Back, Fore, Style

from autollama import utils
from autollama.config import Config
from autollama.logs import logger
from autollama.memory import get_supported_memory_backends

CFG = Config()

def create_config(
    continuous: bool,
    continuous_limit: int,
    ai_settings_file: str,
    skip_reprompt: bool,
    debug: bool,
    memory_type: str,
    browser_name: str,
    allow_downloads: bool,
    workspace_directory: str
) -> None:
    """Update the configuration with the provided arguments."""
    CFG.set_debug_mode(debug)
    CFG.set_continuous_mode(continuous)
    
    if debug:
        logger.typewriter_log("Debug Mode:", Fore.GREEN, "ENABLED")
    
    if continuous:
        logger.typewriter_log("Continuous Mode:", Fore.RED, "ENABLED")
        logger.typewriter_log(
            "WARNING:", Fore.RED,
            "Continuous mode is not recommended. It may cause unintended actions and prolonged AI operation."
        )
        if continuous_limit:
            CFG.set_continuous_limit(continuous_limit)
            logger.typewriter_log("Continuous Limit:", Fore.GREEN, str(continuous_limit))
    elif continuous_limit:
        raise click.UsageError("--continuous-limit can only be used with --continuous")
    
    if memory_type:
        supported_memory = get_supported_memory_backends()
        if memory_type in supported_memory:
            CFG.memory_backend = memory_type
        else:
            logger.typewriter_log(
                "ONLY THE FOLLOWING MEMORY BACKENDS ARE SUPPORTED:",
                Fore.RED, f"{supported_memory}"
            )
            logger.typewriter_log("Defaulting to:", Fore.YELLOW, CFG.memory_backend)
    
    if skip_reprompt:
        logger.typewriter_log("Skip Re-prompt:", Fore.GREEN, "ENABLED")
        CFG.skip_reprompt = True
    
    if ai_settings_file:
        validated, message = utils.validate_yaml_file(ai_settings_file)
        if validated:
            logger.typewriter_log("Using AI Settings File:", Fore.GREEN, ai_settings_file)
            CFG.ai_settings_file = ai_settings_file
            CFG.skip_reprompt = True
        else:
            logger.typewriter_log("FAILED FILE VALIDATION", Fore.RED, message)
            logger.double_check()
            exit(1)
    
    if browser_name:
        CFG.selenium_web_browser = browser_name
    
    if allow_downloads:
        logger.typewriter_log("Native Downloading:", Fore.GREEN, "ENABLED")
        logger.typewriter_log(
            "WARNING:", Fore.YELLOW,
            f"{Back.LIGHTYELLOW_EX}Auto-Llama will be able to download and save files.{Back.RESET} Monitor downloaded files closely."
        )
        logger.typewriter_log(
            "WARNING:", Fore.YELLOW,
            f"{Back.RED + Style.BRIGHT}ALWAYS VERIFY DOWNLOADED FILES BEFORE OPENING!{Style.RESET_ALL}"
        )
        CFG.allow_downloads = True
