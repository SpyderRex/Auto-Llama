"""Task Statuses module."""
from __future__ import annotations

from typing import TYPE_CHECKING, NoReturn

from autollama.commands.command import command
from autollama.logs import logger

if TYPE_CHECKING:
    from autollama.config import Config


@command(
    "task_complete",
    "Task Complete (Shutdown)",
    '"reason": "<reason>"',
)
def task_complete(reason: str, config: Config) -> NoReturn:
    """
    A function that takes in a string and exits the program

    Parameters:
        reason (str): The reason for shutting down.
    Returns:
        A result string from create chat completion. A list of suggestions to
            improve the code.
    """
    logger.info(title="Shutting down...\n", message=reason)
    quit()
