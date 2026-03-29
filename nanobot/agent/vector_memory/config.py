"""Configuration for vector memory system."""

import os
from pathlib import Path
from dataclasses import dataclass, field


@dataclass
class VectorMemoryConfig:
    enabled: bool = True
    chroma_db_path: str = "~/.nanobot/workspace/vector_memory"
    embedding_provider: str = "deepseek"
    embedding_model: str = "deepseek-embedding-v2"
    embedding_dimension: int = 768
    top_k: int = 5
    max_memory_tokens: int = 4096
    persist_directory: str = "~/.nanobot/workspace/vector_memory/chroma_db"

    user_profile_enabled: bool = True
    conversation_enabled: bool = True

    def get_persist_dir(self) -> Path:
        return Path(os.path.expanduser(self.persist_directory))

    def ensure_dirs(self) -> None:
        self.get_persist_dir().mkdir(parents=True, exist_ok=True)


DEFAULT_CONFIG = VectorMemoryConfig()


def get_config() -> VectorMemoryConfig:
    return DEFAULT_CONFIG


def update_config(**kwargs) -> None:
    global DEFAULT_CONFIG
    for key, value in kwargs.items():
        if hasattr(DEFAULT_CONFIG, key):
            setattr(DEFAULT_CONFIG, key, value)
