"""Agent manager for managing Llama agents"""
from __future__ import annotations

from autollama.config import Config
from autollama.llm.base import ChatSequence
from autollama.llm.chat import Message, create_chat_completion
from autollama.singleton import Singleton


class AgentManager(metaclass=Singleton):
    """Agent manager for managing Llama agents"""

    def __init__(self):
        self.next_key = 0
        self.agents: dict[
            int, tuple[str, list[Message], str]
        ] = {}  # key, (task, full_message_history, model)
        self.cfg = Config()

    # Create new Llama agent
    # TODO: Centralise use of create_chat_completion() to globally enforce token limit

    def create_agent(
        self, task: str, creation_prompt: str, model: str
    ) -> tuple[int, str]:
        """Create a new agent and return its key

        Args:
            task: The task to perform
            creation_prompt: Prompt passed to the LLM at creation
            model: The model to use to run this agent

        Returns:
            The key of the new agent
        """
        messages = ChatSequence.for_model(model, [Message("user", creation_prompt)])

        
        # Start Llama instance
        agent_reply = create_chat_completion(prompt=messages)

        messages.add("assistant", agent_reply)

        key = self.next_key
        # This is done instead of len(agents) to make keys unique even if agents
        # are deleted
        self.next_key += 1

        self.agents[key] = (task, list(messages), model)

        return key, agent_reply

    def message_agent(self, key: str | int, message: str) -> str:
        """Send a message to an agent and return its response

        Args:
            key: The key of the agent to message
            message: The message to send to the agent

        Returns:
            The agent's response
        """
        task, messages, model = self.agents[int(key)]

        # Add user message to message history before sending to agent
        messages = ChatSequence.for_model(model, messages)
        messages.add("user", message)

        # Start Llama instance
        agent_reply = create_chat_completion(prompt=messages)

        messages.add("assistant", agent_reply)

        return agent_reply

    def list_agents(self) -> list[tuple[str | int, str]]:
        """Return a list of all agents

        Returns:
            A list of tuples of the form (key, task)
        """

        # Return a list of agent keys and their tasks
        return [(key, task) for key, (task, _, _) in self.agents.items()]

    def delete_agent(self, key: str | int) -> bool:
        """Delete an agent from the agent manager

        Args:
            key: The key of the agent to delete

        Returns:
            True if successful, False otherwise
        """

        try:
            del self.agents[int(key)]
            return True
        except KeyError:
            return False
