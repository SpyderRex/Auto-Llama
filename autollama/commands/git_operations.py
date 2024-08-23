"""Git operations for autollama"""
from typing import TYPE_CHECKING

from git.repo import Repo

from autollama.commands.command import command
from autollama.config import Config
from autollama.url_utils.validators import validate_url

if TYPE_CHECKING:
    from autollama.config import Config


@command(
    "clone_repository",
    "Clone Repository",
    '"url": "<repository_url>", "clone_path": "<clone_path>"',
    lambda config: config.github_username and config.github_api_key,
    "Configure github_username and github_api_key.",
)
@validate_url
def clone_repository(url: str, clone_path: str, config: Config) -> str:
    """Clone a GitHub repository locally.

    Args:
        url (str): The URL of the repository to clone.
        clone_path (str): The path to clone the repository to.

    Returns:
        str: The result of the clone operation.
    """
    split_url = url.split("//")
    auth_repo_url = f"//{config.github_username}:{config.github_api_key}@".join(
        split_url
    )
    try:
        Repo.clone_from(url=auth_repo_url, to_path=clone_path)
        return f"""Cloned {url} to {clone_path}"""
    except Exception as e:
        return f"Error: {str(e)}"
