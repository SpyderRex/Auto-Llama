from autollama.logs import logger
from autollama.memory.local import LocalCache

supported_memory = ["local"]

def get_memory(cfg, init=False):
    memory = LocalCache(cfg)
    
    if init:
        memory.clear()
    return memory

def get_supported_memory_backends():
    return supported_memory

__all__ = [
    "get_memory",
    "LocalCache",
]
