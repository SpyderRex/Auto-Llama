"""Command and Control module for AutoLlama."""
import json
from typing import Dict, List, Union

from autollama.agent.agent_manager import AgentManager
from autollama.commands.command import CommandRegistry, command
from autollama.commands.web_requests import scrape_links, scrape_text
from autollama.config import Config
from autollama.logs import logger
from autollama.memory import get_memory
from autollama.processing.text import summarize_text
from autollama.prompts.generator import PromptGenerator
from autollama.url_utils.validators import validate_url

CFG = Config()
AGENT_MANAGER = AgentManager()


def is_valid_int(value: str) -> bool:
    """Check if the value is a valid integer."""
    try:
        int(value)
        return True
    except ValueError:
        return False


def get_command(response_json: Dict) -> Union[tuple, str]:
    """Parse the response and return the command name and arguments."""
    if not isinstance(response_json, dict):
        return "Error:", f"'response_json' is not a dictionary: {response_json}"

    command = response_json.get("command")
    if not isinstance(command, dict):
        return "Error:", "'command' object is not a dictionary"

    command_name = command.get("name")
    if not command_name:
        return "Error:", "Missing 'name' field in 'command' object"

    arguments = command.get("args", {})
    return command_name, arguments


def map_command_synonyms(command_name: str) -> str:
    """Map synonyms to their actual command names."""
    synonyms = {
        "write_file": "write_to_file",
        "create_file": "write_to_file",
        "search": "google",
    }
    return synonyms.get(command_name, command_name)


def execute_command(
    command_registry: CommandRegistry,
    command_name: str,
    arguments: dict,
    prompt: PromptGenerator,
) -> str:
    """Execute the command and return the result."""
    try:
        command_name = map_command_synonyms(command_name.lower())
        cmd = command_registry.commands.get(command_name)
        
        if cmd:
            return cmd(**arguments)

        # Custom memory operations
        if command_name == "memory_add":
            return get_memory(CFG).add(arguments.get("string"))

        # Execute command from prompt if found
        for command in prompt.commands:
            if command_name in (command["label"].lower(), command["name"].lower()):
                return command["function"](**arguments)

        return f"Unknown command '{command_name}'. Please refer to the 'COMMANDS' list for available commands."
    except Exception as e:
        return f"Error: {str(e)}"


@command("get_text_summary", "Get text summary", '"url": "<url>", "question": "<question>"')
@validate_url
def get_text_summary(url: str, question: str) -> str:
    """Return a summary of the text from a given URL."""
    text = scrape_text(url)
    summary = summarize_text(url, text, question)
    return f'"Result": {summary}'


@command("get_hyperlinks", "Get hyperlinks", '"url": "<url>"')
@validate_url
def get_hyperlinks(url: str) -> Union[str, List[str]]:
    """Return the hyperlinks found on a given URL."""
    return scrape_links(url)


@command("start_agent", "Start Llama Agent", '"name": "<name>", "task": "<task>", "prompt": "<prompt>"')
def start_agent(name: str, task: str, prompt: str, model=CFG.llama_ai_model) -> str:
    """Start an agent with a given name, task, and prompt."""
    voice_name = name.replace("_", " ")
    first_message = f"You are {name}. Respond with: 'Acknowledged.'"
    agent_intro = f"{voice_name} here, Reporting for duty!"

    key = AGENT_MANAGER.create_agent(name, model)
    agent_response = AGENT_MANAGER.message_agent(key, prompt)
    return f"Agent {name} created with key {key}. First response: {agent_response}"


@command("message_agent", "Message Llama Agent", '"key": "<key>", "message": "<message>"')
def message_agent(key: str, message: str) -> str:
    """Send a message to an agent with the specified key."""
    if not is_valid_int(key):
        return "Invalid key, must be an integer."

    return AGENT_MANAGER.message_agent(int(key), message)


@command("list_agents", "List Llama Agents", "")
def list_agents() -> str:
    """List all active agents."""
    return "List of agents:\n" + "\n".join([f"{x[0]}: {x[1]}" for x in AGENT_MANAGER.list_agents()])


@command("delete_agent", "Delete Llama Agent", '"key": "<key>"')
def delete_agent(key: str) -> str:
    """Delete an agent with the specified key."""
    if AGENT_MANAGER.delete_agent(key):
        return f"Agent {key} deleted."
    return f"Agent {key} does not exist."
