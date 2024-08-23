"""Text processing functions"""
from math import ceil
from typing import Optional, List, Tuple

import spacy

from autollama.config import Config
from autollama.llm.base import ChatSequence
from autollama.llm.providers.groq import GROQ_MODELS
from autollama.llm.utils import count_string_tokens, create_chat_completion
from autollama.logs import logger
from autollama.utils import batch

CFG = Config()

def _max_chunk_length(model: str, max: Optional[int] = None) -> int:
    model_max_input_tokens = GROQ_MODELS[model].max_tokens - 1
    max_length = min(max, model_max_input_tokens) if max else model_max_input_tokens
    logger.debug(f"Max chunk length for model {model}: {max_length}")
    return max_length

def must_chunk_content(text: str, for_model: str, max_chunk_length: Optional[int] = None) -> bool:
    tokens = count_string_tokens(text, for_model)
    needs_chunking = tokens > _max_chunk_length(for_model, max_chunk_length)
    logger.debug(f"Text requires chunking: {needs_chunking} (tokens: {tokens})")
    return needs_chunking

def chunk_content(
    content: str,
    for_model: str,
    max_chunk_length: Optional[int] = None,
    with_overlap: bool = True
) -> List[Tuple[str, int]]:
    """Split content into chunks of approximately equal token length."""
    MAX_OVERLAP = 200  # limit overlap to save tokens

    if not must_chunk_content(content, for_model, max_chunk_length):
        length = count_string_tokens(content, for_model)
        logger.debug(f"Content does not require chunking. Length: {length}")
        return [(content, length)]

    max_chunk_length = max_chunk_length or _max_chunk_length(for_model)
    logger.debug(f"Max chunk length set to: {max_chunk_length}")

    # Using spacy for tokenization
    nlp = spacy.load(CFG.browse_spacy_language_model)
    doc = nlp(content)
    tokenized_text = [token.text for token in doc]
    total_length = len(tokenized_text)
    n_chunks = ceil(total_length / max_chunk_length)
    logger.debug(f"Total tokens: {total_length}, Number of chunks: {n_chunks}")

    chunk_length = ceil(total_length / n_chunks)
    overlap = min(max_chunk_length - chunk_length, MAX_OVERLAP) if with_overlap else 0

    chunks = []
    for token_batch in batch(tokenized_text, chunk_length + overlap, overlap):
        chunk = "".join(token_batch)
        chunks.append((chunk, len(token_batch)))
        logger.debug(f"Created chunk of length {len(token_batch)}")

    return chunks

def summarize_text(
    text: str, instruction: Optional[str] = None, question: Optional[str] = None
) -> Tuple[str, Optional[List[Tuple[str, str]]]]:
    """Summarize text using the Groq API."""
    if not text:
        raise ValueError("No text to summarize")

    if instruction and question:
        raise ValueError("Parameters 'question' and 'instructions' cannot both be set")

    model = CFG.llm_model

    if question:
        instruction = (
            f'include any information that can be used to answer the question "{question}". '
            "Do not directly answer the question itself."
        )

    summarization_prompt = ChatSequence.for_model(model)

    token_length = count_string_tokens(text, model)
    logger.info(f"Text length: {token_length} tokens")

    max_chunk_length = _max_chunk_length(model) - 550
    logger.info(f"Max chunk length: {max_chunk_length} tokens")

    if not must_chunk_content(text, model, max_chunk_length):
        summarization_prompt.add(
            "user",
            "Write a concise summary of the following text"
            f"{f'; {instruction}' if instruction else ''}:"
            "\n\n\n"
            f'LITERAL TEXT: """{text}"""'
            "\n\n\n"
            "CONCISE SUMMARY: The text is best summarized as"
        )

        logger.debug(f"Summarizing with {model}:\n{summarization_prompt.dump()}\n")
        summary = create_chat_completion(
            summarization_prompt, temperature=0, max_tokens=500
        )

        logger.debug(f"\n{'-'*16} SUMMARY {'-'*17}\n{summary}\n{'-'*42}\n")
        return summary.strip(), None

    summaries: List[str] = []
    chunks = list(split_text(text, for_model=model, max_chunk_length=max_chunk_length))

    for i, (chunk, chunk_length) in enumerate(chunks):
        logger.info(
            f"Summarizing chunk {i + 1} / {len(chunks)} of length {chunk_length} tokens"
        )
        summary, _ = summarize_text(chunk, instruction)
        summaries.append(summary)

    logger.info(f"Summarized {len(chunks)} chunks")

    final_summary, _ = summarize_text("\n\n".join(summaries))

    return final_summary.strip(), [
        (summaries[i], chunks[i][0]) for i in range(len(chunks))
    ]

def split_text(
    text: str,
    for_model: str = CFG.llm_model,
    with_overlap: bool = True,
    max_chunk_length: Optional[int] = None,
) -> List[Tuple[str, int]]:
    """Split text into chunks of sentences, with each chunk not exceeding the maximum length."""
    max_length = _max_chunk_length(for_model, max_chunk_length)

    # Flatten paragraphs to improve performance
    text = text.replace("\n", " ")
    text_length = count_string_tokens(text, for_model)
    logger.debug(f"Text length after flattening: {text_length} tokens")

    if text_length < max_length:
        logger.debug(f"Text is short enough to not require splitting.")
        return [(text, text_length)]

    n_chunks = ceil(text_length / max_length)
    target_chunk_length = ceil(text_length / n_chunks)
    logger.debug(f"Target chunk length: {target_chunk_length} tokens")

    nlp = spacy.load(CFG.browse_spacy_language_model)
    nlp.add_pipe("sentencizer")
    doc = nlp(text)
    sentences = [sentence.text.strip() for sentence in doc.sents]

    chunks = []
    current_chunk = []
    current_chunk_length = 0
    last_sentence = None
    last_sentence_length = 0

    i = 0
    while i < len(sentences):
        sentence = sentences[i]
        sentence_length = count_string_tokens(sentence, for_model)
        expected_chunk_length = current_chunk_length + 1 + sentence_length

        if (
            expected_chunk_length < max_length
            and (expected_chunk_length - sentence_length / 2) < target_chunk_length
        ):
            current_chunk.append(sentence)
            current_chunk_length = expected_chunk_length

        elif sentence_length < max_length:
            if last_sentence:
                chunks.append((" ".join(current_chunk), current_chunk_length))
                current_chunk = []
                current_chunk_length = 0

                if with_overlap:
                    overlap_max_length = max_length - sentence_length - 1
                    if last_sentence_length < overlap_max_length:
                        current_chunk += [last_sentence]
                        current_chunk_length += last_sentence_length + 1
                    elif overlap_max_length > 5:
                        current_chunk += [
                            list(
                                chunk_content(
                                    last_sentence,
                                    for_model,
                                    overlap_max_length,
                                )
                            ).pop()[0],
                        ]
                        current_chunk_length += overlap_max_length + 1

            current_chunk += [sentence]
            current_chunk_length += sentence_length

        else:  # Sentence longer than maximum length -> chop up and try again
            sentences[i : i + 1] = [
                chunk
                for chunk, _ in chunk_content(sentence, for_model, target_chunk_length)
            ]
            continue

        i += 1
        last_sentence = sentence
        last_sentence_length = sentence_length

    if current_chunk:
        chunks.append((" ".join(current_chunk), current_chunk_length))
    
    logger.debug(f"Total chunks created: {len(chunks)}")
    return chunks
