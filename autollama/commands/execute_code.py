import os
import subprocess
from pathlib import Path
import venv
import shutil

from autollama.commands.command import command
from autollama.config import Config
from autollama.logs import logger

CFG = Config()

VENV_DIR = "code_execution_venv"


@command("execute_python_file", "Execute Python File", '"filename": "<filename>"')
def execute_python_file(filename: str) -> str:
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

    try:
        # Create a virtual environment for code execution
        venv_path = os.path.join(CFG.workspace_path, VENV_DIR)
        if not os.path.exists(venv_path):
            logger.info(f"Creating virtual environment at '{venv_path}'")
            venv.create(venv_path, with_pip=True)

        # Install any required packages (if needed)
        activate_script = os.path.join(venv_path, 'bin', 'activate')
        requirements_file = os.path.join(CFG.workspace_path, 'requirements.txt')
        if os.path.exists(requirements_file):
            subprocess.run(f'source {activate_script} && pip install -r {requirements_file}', shell=True)

        # Execute the Python file within the virtual environment
        result = subprocess.run(
            f'source {activate_script} && python {filename}',
            capture_output=True, encoding="utf8", shell=True
        )
        if result.returncode == 0:
            return result.stdout
        else:
            return f"Error: {result.stderr}"

    except Exception as e:
        return f"Error: {str(e)}"

    finally:
        # Cleanup virtual environment after execution
        if os.path.exists(venv_path):
            logger.info(f"Removing virtual environment at '{venv_path}'")
            shutil.rmtree(venv_path)


@command(
    "execute_shell",
    "Execute Shell Command, non-interactive commands only",
    '"command_line": "<command_line>"',
    CFG.execute_local_commands,
    "You are not allowed to run local shell commands. To execute"
    " shell commands, EXECUTE_LOCAL_COMMANDS must be set to 'True' "
    "in your config. Do not attempt to bypass the restriction.",
)
def execute_shell(command_line: str) -> str:
    """Execute a shell command and return the output

    Args:
        command_line (str): The command line to execute

    Returns:
        str: The output of the command
    """

    current_dir = Path.cwd()
    # Change dir into workspace if necessary
    if not current_dir.is_relative_to(CFG.workspace_path):
        os.chdir(CFG.workspace_path)

    logger.info(
        f"Executing command '{command_line}' in working directory '{os.getcwd()}'"
    )

    result = subprocess.run(command_line, capture_output=True, shell=True)
    output = f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"

    # Change back to whatever the prior working dir was

    os.chdir(current_dir)
    return output


@command(
    "execute_shell_popen",
    "Execute Shell Command, non-interactive commands only",
    '"command_line": "<command_line>"',
    CFG.execute_local_commands,
    "You are not allowed to run local shell commands. To execute"
    " shell commands, EXECUTE_LOCAL_COMMANDS must be set to 'True' "
    "in your config. Do not attempt to bypass the restriction.",
)
def execute_shell_popen(command_line) -> str:
    """Execute a shell command with Popen and returns an english description
    of the event and the process id

    Args:
        command_line (str): The command line to execute

    Returns:
        str: Description of the fact that the process started and its id
    """

    current_dir = os.getcwd()
    # Change dir into workspace if necessary
    if CFG.workspace_path not in current_dir:
        os.chdir(CFG.workspace_pth)

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
        bool: True if we are running in a Docker container, False otherwise
    """
    return False  # This is no longer needed, so it always returns False
