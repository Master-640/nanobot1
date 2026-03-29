"""Vector memory hook for automatic memory retrieval and storage."""

import asyncio
from typing import Any

from loguru import logger

from nanobot.agent.hook import AgentHook, AgentHookContext
from nanobot.agent.vector_memory.chromadb_store import ChromaDBStore
from nanobot.agent.vector_memory.config import get_config
from nanobot.agent.vector_memory.embedding_service import EmbeddingService
from nanobot.agent.vector_memory.retrieval import VectorRetrieval


class VectorMemoryHook:
    """Hook for automatic vector memory retrieval and storage."""

    MEMORY_INJECTION_MARKER = "\n\n[MEMORY_INJECTED_BY_VECTOR_SYSTEM]\n"

    def __init__(self, api_key: str | None = None):
        config = get_config()
        if not config.enabled:
            self._disabled = True
            return

        self._disabled = False
        self._embedding_service = EmbeddingService(api_key=api_key)
        self._store = ChromaDBStore()
        self._retrieval = VectorRetrieval(
            embedding_service=self._embedding_service,
            store=self._store,
        )
        self._config = config
        self._session_key = "cli:direct"
        self._initialized = False

    async def _ensure_initialized(self) -> None:
        if self._initialized:
            return
        self._store._ensure_collections()
        self._initialized = True

    async def retrieve_memory(self, query: str) -> str:
        if self._disabled:
            return ""

        await self._ensure_initialized()

        try:
            retrieved = await self._retrieval.retrieve(
                query=query,
                collection_type="conversation",
                top_k=self._config.top_k,
            )
            return self._retrieval.format_memory_for_context(
                retrieved,
                max_items=self._config.top_k,
            )
        except Exception as e:
            logger.error(f"Vector memory retrieval failed: {e}")
            return ""

    async def store_conversation(
        self,
        role: str,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        if self._disabled:
            return

        if not content or len(content.strip()) < 5:
            return

        await self._ensure_initialized()

        try:
            self._store.add_conversation(
                session_key=self._session_key,
                role=role,
                content=content,
                metadata=metadata,
            )
        except Exception as e:
            logger.error(f"Vector memory storage failed: {e}")

    def set_session_key(self, session_key: str) -> None:
        self._session_key = session_key


class VectorMemoryManager:
    """Manager that coordinates vector memory retrieval and storage with AgentLoop."""

    def __init__(self, api_key: str | None = None):
        self.hook = VectorMemoryHook(api_key=api_key)
        self._lock = asyncio.Lock()

    async def inject_memory(self, messages: list[dict[str, Any]], session_key: str) -> list[dict[str, Any]]:
        if self.hook._disabled:
            return messages

        self.hook.set_session_key(session_key)

        if not messages:
            return messages

        user_query = ""
        for msg in reversed(messages):
            if msg.get("role") == "user":
                user_query = msg.get("content", "")
                break

        if not user_query:
            return messages

        memory_context = await self.hook.retrieve_memory(user_query)

        if not memory_context:
            return messages

        injected_content = (
            f"{VectorMemoryHook.MEMORY_INJECTION_MARKER}"
            f"{memory_context}\n"
            f"[/MEMORY_INJECTED_BY_VECTOR_SYSTEM]\n\n"
        )

        for msg in messages:
            if msg.get("role") == "system":
                original_content = msg.get("content", "")
                msg["content"] = original_content + "\n\n" + injected_content
                logger.info("Injected vector memory into system prompt")
                return messages

        messages.insert(0, {
            "role": "system",
            "content": injected_content,
        })
        logger.info("Added vector memory as system message")

        return messages

    async def store_turn(
        self,
        role: str,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        await self.hook.store_conversation(
            role=role,
            content=content,
            metadata=metadata,
        )
