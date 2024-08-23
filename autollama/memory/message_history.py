from __future__ import annotations

import copy
import json
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from autogpt.agent import Agent

from autollama.config import Config
from autollama.json_utils.utilities import (
    LLM_DEFAULT_RESPONSE_FORMAT,
    is_string_valid_json,
)
from autollama.llm.base import ChatSequence, Message, MessageRole, MessageType
from autollama.llm.utils import create_chat_completion
from autollama.log_cycle.log_cycle import PROMPT_SUMMARY_FILE_NAME, SUMMARY_FILE_NAME
from autollama.logs import logger


@dataclass
class MessageHistory:
    agent: Agent
    messages: list[Message] = field(default_factory=list)
    summary: str = "I was created"
    last_trimmed_index: int = 0

    def __getitem__(self, i: int):
        logger.debug(f"Accessing message at index {i}")
        return self.messages[i]

    def __iter__(self):
        logger.debug("Iterating over all messages")
        return iter(self.messages)

    def __len__(self):
        logger.debug(f"Getting the length of messages: {len(self.messages)}")
        return len(self.messages)

    def add(
        self,
        role: MessageRole,
        content: str,
        type: MessageType | None = None,
    ):
        logger.debug(f"Adding a new message with role {role} and content: {content}")
        return self.append(Message(role, content, type))

    def append(self, message: Message):
        logger.debug(f"Appending message: {message}")
        self.messages.append(message)

    def trim_messages(
        self,
        current_message_chain: list[Message],
    ) -> tuple[Message, list[Message]]:
        logger.debug("Trimming messages not in the current message chain")
        new_messages = [
            msg for i, msg in enumerate(self) if i > self.last_trimmed_index
        ]
        new_messages_not_in_chain = [
            msg for msg in new_messages if msg not in current_message_chain
        ]

        if not new_messages_not_in_chain:
            logger.debug("No new messages to trim")
            return self.summary_message(), []

        new_summary_message = self.update_running_summary(
            new_events=new_messages_not_in_chain
        )

        last_message = new_messages_not_in_chain[-1]
        self.last_trimmed_index = self.messages.index(last_message)
        logger.debug(
            f"Updated last_trimmed_index to {self.last_trimmed_index} after trimming"
        )

        return new_summary_message, new_messages_not_in_chain

    def per_cycle(self, messages: list[Message] | None = None):
        logger.debug("Iterating over message cycles")
        messages = messages or self.messages
        for i in range(0, len(messages) - 1):
            ai_message = messages[i]
            if ai_message.type != "ai_response":
                continue
            user_message = (
                messages[i - 1] if i > 0 and messages[i - 1].role == "user" else None
            )
            result_message = messages[i + 1]
            try:
                assert is_string_valid_json(
                    ai_message.content, LLM_DEFAULT_RESPONSE_FORMAT
                ), "AI response is not a valid JSON object"
                assert result_message.type == "action_result"
                logger.debug(f"Yielding valid cycle messages: {ai_message}, {result_message}")
                yield user_message, ai_message, result_message
            except AssertionError as err:
                logger.debug(
                    f"Invalid item in message history: {err}; Messages: {messages[i-1:i+2]}"
                )

    def summary_message(self) -> Message:
        logger.debug(f"Returning summary message: {self.summary}")
        return Message(
            "system",
            f"This reminds you of these events from your past: \n{self.summary}",
        )

    def update_running_summary(self, new_events: list[Message]) -> Message:
        logger.debug("Updating running summary with new events")
        cfg = Config()

        if not new_events:
            logger.debug("No new events to summarize.")
            return self.summary_message()

        new_events = copy.deepcopy(new_events)

        for event in new_events:
            if event.role.lower() == "assistant":
                event.role = "you"
                try:
                    content_dict = json.loads(event.content)
                    if "thoughts" in content_dict:
                        del content_dict["thoughts"]
                    event.content = json.dumps(content_dict)
                except json.decoder.JSONDecodeError:
                    logger.error(f"Error: Invalid JSON: {event.content}\n")

            elif event.role.lower() == "system":
                event.role = "your computer"

            elif event.role == "user":
                new_events.remove(event)

        prompt = f'''Your task is to create a concise running summary of actions and information results in the provided text, focusing on key and potentially important information to remember.

You will receive the current summary and the your latest actions. Combine them, adding relevant key information from the latest development in 1st person past tense and keeping the summary concise.

Summary So Far:
"""
{self.summary}
"""

Latest Development:
"""
{new_events or "Nothing new happened."}
"""
'''

        prompt = ChatSequence.for_model(cfg.llm_model, [Message("user", prompt)])
        self.agent.log_cycle_handler.log_cycle(
            self.agent.config.ai_name,
            self.agent.created_at,
            self.agent.cycle_count,
            prompt.raw(),
            PROMPT_SUMMARY_FILE_NAME,
        )

        self.summary = create_chat_completion(prompt)
        logger.debug(f"Updated summary: {self.summary}")

        self.agent.log_cycle_handler.log_cycle(
            self.agent.config.ai_name,
            self.agent.created_at,
            self.agent.cycle_count,
            self.summary,
            SUMMARY_FILE_NAME,
        )

        return self.summary_message()
