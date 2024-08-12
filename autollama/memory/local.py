from __future__ import annotations

import dataclasses
import sqlite3
from pathlib import Path
from typing import Any, List

from autollama.memory.base import MemoryProviderSingleton


@dataclasses.dataclass
class CacheContent:
    texts: List[str] = dataclasses.field(default_factory=list)


class LocalCache(MemoryProviderSingleton):
    def __init__(self, cfg) -> None:
        workspace_path = Path(cfg.workspace_path)
        self.db_path = workspace_path / f"{cfg.memory_index}.db"

        self.connection = sqlite3.connect(self.db_path)
        self.cursor = self.connection.cursor()

        self._initialize_database()

    def _initialize_database(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                text TEXT NOT NULL
            )
        ''')
        self.connection.commit()

    def add(self, text: str):
        if "Command Error:" in text:
            return ""
        self.cursor.execute('''
            INSERT INTO cache (text) VALUES (?)
        ''', (text,))
        self.connection.commit()
        return text

    def clear(self) -> str:
        self.cursor.execute('''
            DELETE FROM cache
        ''')
        self.connection.commit()
        return "Obliviated"

    def get(self, data: str) -> list[Any] | None:
        return self.get_relevant(data, 1)

    def get_relevant(self, text: str, k: int) -> list[Any]:
        # This method simply retrieves the most recent `k` texts from the database
        self.cursor.execute('''
            SELECT text FROM cache
            ORDER BY id DESC
            LIMIT ?
        ''', (k,))
        rows = self.cursor.fetchall()
        return [row[0] for row in rows]

    def get_stats(self) -> tuple[int, tuple[int, ...]]:
        self.cursor.execute('''
            SELECT COUNT(*) FROM cache
        ''')
        count = self.cursor.fetchone()[0]
        return count, (0,)


    def __del__(self):
        self.connection.close()
