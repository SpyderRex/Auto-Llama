import abc
import functools
from typing import MutableSet, Sequence, Optional

import numpy as np

from autollama.config.config import Config
from autollama.logs import logger
from autollama.singleton import AbstractSingleton

from .. import MemoryItem, MemoryItemRelevance
from ..utils import Embedding, get_embedding


class VectorMemoryProvider(MutableSet[MemoryItem], AbstractSingleton):
    def __init__(self, config: Config):
        super().__init__()
        self.config = config

    def get(self, query: str) -> Optional[MemoryItemRelevance]:
        """
        Retrieves the most relevant memory item for the given query.

        Args:
            query: The query to compare stored memories to.

        Returns:
            The most relevant MemoryItemRelevance or None if no relevant memories are found.
        """
        results = self.get_relevant(query, 1)
        return results[0] if results else None

    def get_relevant(self, query: str, k: int) -> Sequence[MemoryItemRelevance]:
        """
        Retrieves the top-k most relevant memory items for the given query.

        Args:
            query: The query to compare stored memories to.
            k: The number of relevant memories to fetch.

        Returns:
            A list of the top-k MemoryItemRelevance objects.
        """
        if not self:
            return []

        logger.debug(
            f"Searching for {k} relevant memories for query '{query}'; "
            f"{len(self)} memories in index"
        )

        relevances = self.score_memories_for_relevance(query)
        logger.debug(f"Memory relevance scores: {[str(r) for r in relevances]}")

        # Sort by relevance score and get the top k
        top_k_indices = np.argsort([-r.score for r in relevances])[:k]
        return [relevances[i] for i in top_k_indices]

    def score_memories_for_relevance(self, for_query: str) -> Sequence[MemoryItemRelevance]:
        """
        Scores all memories in the index for relevance to the given query.

        Args:
            for_query: The query to compare stored memories to.

        Returns:
            A list of MemoryItemRelevance objects for each memory in the index.
        """
        e_query: Embedding = get_embedding(for_query)
        return [m.relevance_for(for_query, e_query) for m in self]

    def get_stats(self) -> tuple[int, int]:
        """
        Returns statistics about the memory index.

        Returns:
            A tuple (n_memories, n_chunks) where n_memories is the number of memories and
            n_chunks is the total number of chunks across all memories.
        """
        n_memories = len(self)
        n_chunks = sum(len(m.e_chunks) for m in self)
        return n_memories, n_chunks
