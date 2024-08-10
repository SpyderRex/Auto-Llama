import time
from random import shuffle

from autollama.config import Config
from autollama.llm.base import Message
from autollama.llm.llm_utils import create_chat_completion
from autollama.llm.token_counter import count_message_tokens
from autollama.log_cycle.log_cycle import CURRENT_CONTEXT_FILE_NAME
from autollama.logs import logger

cfg = Config()

def create_chat_message(role, content) -> Message:
    """
    Create a chat message with the given role and content.

    Args:
    role (str): The role of the message sender, e.g., "system", "user", or "assistant".
    content (str): The content of the message.

    Returns:
    dict: A dictionary containing the role and content of the message.
    """
    return {"role": role, "content": content}

def generate_context(prompt, relevant_memory, full_message_history, model):
    current_context = [
        create_chat_message("system", prompt),
        create_chat_message(
            "system", f"The current time and date is {time.strftime('%c')}"
        ),
    ]

    next_message_to_add_index = len(full_message_history) - 1
    insertion_index = len(current_context)
    current_tokens_used = count_message_tokens(current_context)
    return (
        next_message_to_add_index,
        current_tokens_used,
        insertion_index,
        current_context,
    )

def chat_with_ai(
    agent, prompt, user_input, full_message_history, permanent_memory, token_limit
):
    """Interact with the Llama3 model using the Groq API, sending the prompt, user input, message history,
    and permanent memory."""
    while True:
        try:
            model = cfg.llama_ai_model
            send_token_limit = token_limit - 1000
            relevant_memory = ""
            logger.debug(f"Memory Stats: {permanent_memory.get_stats()}")

            (
                next_message_to_add_index,
                current_tokens_used,
                insertion_index,
                current_context,
            ) = generate_context(prompt, relevant_memory, full_message_history, model)

            current_tokens_used += count_message_tokens(
                [create_chat_message("user", user_input)]
            )

            current_tokens_used += 500  # Account for memory (appended later)

            while next_message_to_add_index >= 0:
                message_to_add = full_message_history[next_message_to_add_index]

                tokens_to_add = count_message_tokens([message_to_add])
                if current_tokens_used + tokens_to_add > send_token_limit:
                    break

                current_context.insert(
                    insertion_index, full_message_history[next_message_to_add_index]
                )

                current_tokens_used += tokens_to_add
                next_message_to_add_index -= 1

            from autollama.memory_management.summary_memory import (
                get_newly_trimmed_messages,
                update_running_summary,
            )

            if len(full_message_history) > 0:
                (
                    newly_trimmed_messages,
                    agent.last_memory_index,
                ) = get_newly_trimmed_messages(
                    full_message_history=full_message_history,
                    current_context=current_context,
                    last_memory_index=agent.last_memory_index,
                )

                agent.summary_memory = update_running_summary(
                    agent,
                    current_memory=agent.summary_memory,
                    new_events=newly_trimmed_messages,
                )
                current_context.insert(insertion_index, agent.summary_memory)

            # Append user input, the length of this is accounted for above
            current_context.extend([create_chat_message("user", user_input)])

            tokens_remaining = token_limit - current_tokens_used

            logger.debug(f"Token limit: {token_limit}")
            logger.debug(f"Send Token Count: {current_tokens_used}")
            logger.debug(f"Tokens remaining for respnse: {tokens_remaining}")
            logger.debug("------------ CONTEXT SENT TO AI ---------------")
            for message in current_context:
                if message["role"] == "system" and message["content"] == prompt:
                    continue
                logger.debug(f"{message['role'].capitalize()}: {message['content']}")
                logger.debug("")
            logger.debug("----------- END OF CONTEXT ----------------")
            agent.log_cycle_handler.log_cycle(
                agent.config.ai_name,
                agent.created_at,
                agent.cycle_count,
                current_context,
                CURRENT_CONTEXT_FILE_NAME,
            )

            assistant_reply = create_chat_completion(
                model=cfg.llama_ai_model,
                messages=current_context,
                max_tokens=tokens_remaining,
            )

            full_message_history.append(create_chat_message("user", user_input))
            full_message_history.append(
                create_chat_message("assistant", assistant_reply)
            )

            return assistant_reply
        except Exception as e:
            logger.warn("Error: ", f"{e}")
            time.sleep(10)
