from typing import Any, List, Union, overload
import numpy as np
import spacy
from autollama.config import Config
from autollama.logs import logger

# Define the Embedding type
Embedding = Union[List[np.float32], np.ndarray[Any, np.dtype[np.float32]]]
TText = List[int]  # Token array representing text

# Load the Spacy model once using the model defined in the config
cfg = Config()
nlp = spacy.load(cfg.embedding_model)

@overload
def get_embedding(input: str) -> Embedding: ...

@overload
def get_embedding(input: TText) -> Embedding: ...

@overload
def get_embedding(input: List[str]) -> List[Embedding]: ...

@overload
def get_embedding(input: List[TText]) -> List[Embedding]: ...

def get_embedding(
    input: Union[str, TText, List[str], List[TText]]
) -> Union[Embedding, List[Embedding]]:
    """
    Get an embedding from the Spacy model.

    Args:
        input: Input text(s) to get embeddings for, either as a string, array of tokens,
               or lists of strings or token arrays.

    Returns:
        Embedding or List[Embedding]: The resulting embedding(s) from the Spacy model.
    """
    multiple = isinstance(input, list) and not isinstance(input[0], int)

    if isinstance(input, str):
        input = input.replace("\n", " ")
    elif multiple and isinstance(input[0], str):
        input = [text.replace("\n", " ") for text in input]

    logger.debug(
        f"Getting embedding{'s' if multiple else ''} "
        f"for {'multiple inputs' if multiple else 'a single input'} "
        f"with Spacy model '{cfg.embedding_model}'"
    )

    if multiple:
        # Process a list of inputs using Spacy's pipeline for efficiency
        return [doc.vector.tolist() for doc in nlp.pipe(input)]
    else:
        # Process a single input
        return nlp(input).vector.tolist()
