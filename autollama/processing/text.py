import re
from typing import Dict, Generator, Optional
import itertools

import nltk
from selenium.webdriver.remote.webdriver import WebDriver

from autollama.config import Config
from autollama.llm import count_message_tokens, create_chat_completion
from autollama.logs import logger
from autollama.memory import get_memory

CFG = Config()


def split_text(
    text: str,
    max_length: int = CFG.browse_chunk_max_length,
    model: str = CFG.llama_ai_model,
    question: str = "",
) -> Generator[str, None, None]:
    """Split text into chunks that fit within the model's token limit.

    Args:
        text (str): The text to split.
        max_length (int): Maximum length of tokens per chunk.
        model (str): The model used for token counting.
        question (str): The question associated with the text.

    Yields:
        Generator[str, None, None]: Chunks of text.
    """
    logger.debug(f"Original text length: {len(text)} characters")
    
    flattened_paragraphs = re.sub(r"\s+", " ", text)
    sentences = nltk.sent_tokenize(flattened_paragraphs)

    current_chunk = []

    for sentence in sentences:
        current_chunk.append(sentence)
        message_with_current_chunk = [create_message(" ".join(current_chunk), question)]

        expected_token_usage = (
            count_message_tokens(messages=message_with_current_chunk, model=model)
            + 1
        )
        if expected_token_usage > max_length:
            current_chunk.pop()
            if not current_chunk:
                raise ValueError("A sentence is too long to fit in a chunk.")
            logger.debug(f"Yielding chunk of length {len(' '.join(current_chunk))} characters")
            yield " ".join(current_chunk)
            current_chunk = [sentence]

    if current_chunk:
        logger.debug(f"Yielding final chunk of length {len(' '.join(current_chunk))} characters")
        yield " ".join(current_chunk)


def summarize_text(
    url: str, text: str, question: str, driver: Optional[WebDriver] = None
) -> str:
    """Summarize text by breaking it into chunks, processing each chunk, and combining the results.

    Args:
        url (str): URL of the source.
        text (str): The text to summarize.
        question (str): The question to answer based on the text.
        driver (Optional[WebDriver]): WebDriver for scrolling, if needed.

    Returns:
        str: The combined summary of the text.
    """
    if not text:
        return "Error: No text to summarize"
    
    logger.debug(f"Summarizing text of length {len(text)} characters from URL: {url}")

    summaries = []
    chunks = list(split_text(
        text, max_length=CFG.browse_chunk_max_length, model=CFG.llama_ai_model, question=question
    ))
    logger.debug(f"Number of chunks: {len(chunks)}")

    scroll_ratio = 1 / len(chunks) if chunks else 1

    for i, chunk in enumerate(chunks):
        if driver:
            scroll_to_percentage(driver, scroll_ratio * i)
        
        logger.debug(f"Processing chunk {i + 1} / {len(chunks)} with length {len(chunk)} characters")

        memory_to_add = f"Source: {url}\n" + chunk
        memory = get_memory(CFG)
        memory.add(memory_to_add)

        messages = [create_message(chunk, question)]
        tokens_for_chunk = count_message_tokens(messages, CFG.llama_ai_model)
        logger.debug(f"Tokens for chunk {i + 1}: {tokens_for_chunk}")

        summary = create_chat_completion(
            model=CFG.llama_ai_model,
            messages=messages,
        )
        summaries.append(summary)
        logger.debug(f"Chunk {i + 1} summary length: {len(summary)} characters")

        memory_to_add = f"Source: {url}\nContent summary part#{i + 1}: {summary}"
        logger.debug(f"Adding to memory: {repr(memory_to_add)}")  # Use repr() to handle special characters
        memory.add(memory_to_add)

    combined_summary = "\n".join(summaries)
    logger.debug(f"Combined summary length: {len(combined_summary)} characters")
    messages = [create_message(combined_summary, question)]
    final_summary = create_chat_completon(
        model=CFG.llama_ai_model,
        messages=messages,
    )
    logger.debug(f"Final summary length: {len(final_summary)} characters")
    
    return final_summary


def scroll_to_percentage(driver: WebDriver, ratio: float) -> None:
    """Scroll the page to a given percentage.

    Args:
        driver (WebDriver): The Selenium WebDriver instance.
        ratio (float): The percentage to scroll to (0 to 1).

    Raises:
        ValueError: If ratio is out of bounds.
    """
    if ratio < 0 or ratio > 1:
        raise ValueError("Percentage should be between 0 and 1")
    logger.debug(f"Scrolling to {ratio * 100}%")
    driver.execute_script(f"window.scrollTo(0, document.body.scrollHeight * {ratio});")


def create_message(chunk: str, question: str) -> Dict[str, str]:
    """Create a message dictionary for the chat model.

    Args:
        chunk (str): The text chunk.
        question (str): The question related to the chunk.

    Returns:
        Dict[str, str]: The message dictionary.
    """
    message = {
        "role": "user",
        "content": f'"""{chunk}""" Using the above text, answer the following'
                   f' question: "{question}" -- if the question cannot be answered using the text,'
                   " summarize the text.",
    }
    logger.debug(f"Created message: {repr(message)}")  # Use repr() to handle special characters
    return message
