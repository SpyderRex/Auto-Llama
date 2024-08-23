import os
import subprocess
from pathlib import Path

from autollama.commands.command import command
from autollama.config import Config
from autollama.logs import logger


@command("execute_python_file", "Execute Python File", '"filename": "<filename>"')
def execute_python_file(filename: str, config: Config) -> str:
    """Execute a Python file in a virtual environment and return the output

    Args:
        filename (str): The name of the file to execute

    Returns:
        str: The output of the file
    """
    logger.info(f"Executing file '{filename}'")

    if not filename.endswith(".py"):
        return "Error: Invalid file type. Only .py files are allowed."

    if not os.path.isfile(filename):
        return f"Error: File '{filename}' does not exist."

    venv_path = os.path.join(config.workspace_path, "venv")
    if not os.path.exists(venv_path):
        return f"Error: Virtual environment not found at '{venv_path}'. Please set up the virtual environment."

    venv_python = os.path.join(venv_path, "bin", "python")
    if not os.path.exists(venv_python):
        return f"Error: Python executable not found in the virtual environment."

    result = subprocess.run(
        [venv_python, filename], capture_output=True, encoding="utf8"
    )
    if result.returncode == 0:
        return result.stdout
    else:
        return f"Error: {result.stderr}"


def validate_command(command: str, config: Config) -> bool:
    """Validate a command to ensure it is allowed

    Args:
        command (str): The command to validate

    Returns:
        bool: True if the command is allowed, False otherwise
    """
    tokens = command.split()

    if not tokens:
        return False

    if config.deny_commands and tokens[0] not in config.deny_commands:
        return False

    for keyword in config.allow_commands:
        if keyword in tokens:
            return True
    if config.allow_commands:
        return False

    return True


@command(
    "execute_shell",
    "Execute Shell Command, non-interactive commands only",
    '"command_line": "<command_line>"',
    lambda cfg: cfg.execute_local_commands,
    "You are not allowed to run local shell commands. To execute"
    " shell commands, EXECUTE_LOCAL_COMMANDS must be set to 'True' "
    "in your config file: .env - do not attempt to bypass the restriction.",
)
def execute_shell(command_line: str, config: Config) -> str:
    """Execute a shell command and return the output

    Args:
        command_line (str): The command line to execute

    Returns:
        str: The output of the command
    """
    if not validate_command(command_line, config):
        logger.info(f"Command '{command_line}' not allowed")
        return "Error: This Shell Command is not allowed."

    current_dir = Path.cwd()
    # Change dir into workspace if necessary
    if not current_dir.is_relative_to(config.workspace_path):
        os.chdir(config.workspace_path)

    logger.info(
        f"Executing command '{command_line}' in working directory '{os.getcwd()}'"
    )

    result = subprocess.run(command_line, capture_output=True, shell=True)
    output = f"STDOUT:\n{result.stdout.decode('utf-8')}\nSTDERR:\n{result.stderr.decode('utf-8')}"

    # Change back to whatever the prior working dir was
    os.chdir(current_dir)
    return output


@command(
    "execute_shell_popen",
    "Execute Shell Command, non-interactive commands only",
    '"command_line": "<command_line>"',
    lambda config: config.execute_local_commands,
    "You are not allowed to run local shell commands. To execute"
    " shell commands, EXECUTE_LOCAL_COMMANDS must be set to 'True' "
    "in your config. Do not attempt to bypass the restriction.",
)
def execute_shell_popen(command_line, config: Config) -> str:
    """Execute a shell command with Popen and returns an English description
    of the event and the process id

    Args:
        command_line (str): The command line to execute

    Returns:
        str: Description of the fact that the process started and its id
    """
    if not validate_command(command_line, config):
        logger.info(f"Command '{command_line}' not allowed")
        return "Error: This Shell Command is not allowed."

    current_dir = os.getcwd()
    # Change dir into workspace if necessary
    if config.workspace_path not in current_dir:
        os.chdir(config.workspace_path)

    logger.info(
        f"Executing command '{command_line}' in working directory '{os.getcwd()}'"
    )

    do_not_show_output = subprocess.DEVNULL
    process = subprocess.Popen(
        command_line, shell=True, stdout=do_not_show_output, stderr=do_not_show_output
    )

    # Change back to whatever the prior working dir was
    os.chdir(current_dir)

    return f"Subprocess started with PID:'{str(process.pid)}'"


def we_are_running_in_a_docker_container() -> bool:
    """Check if we are running in a Docker container

    Returns:
        bool: False as Docker is not being used
    """
    return False
