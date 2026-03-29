"""Vector retrieval logic for memory system."""

from typing import Any

from loguru import logger

from nanobot.agent.vector_memory.chromadb_store import ChromaDBStore
from nanobot.agent.vector_memory.config import get_config
from nanobot.agent.vector_memory.embedding_service import EmbeddingService


class VectorRetrieval:
    def __init__(
        self,
        embedding_service: EmbeddingService,
        store: ChromaDBStore,
    ):
        self.embedding_service = embedding_service
        self.store = store
        self.config = get_config()

    async def retrieve(
        self,
        query: str,
        collection_type: str = "conversation",
        top_k: int | None = None,
    ) -> list[dict[str, Any]]:
        k = top_k or self.config.top_k

        query_embedding = await self.embedding_service.embed_single(query)

        if not query_embedding:
            logger.warning("Failed to get embedding for query")
            return []

        collection_name = (
            ChromaDBStore.COLLECTION_CONVERSATION
            if collection_type == "conversation"
            else ChromaDBStore.COLLECTION_USER_PROFILE
        )

        try:
            results = self.store.query(
                collection_name=collection_name,
                query_embeddings=[query_embedding],
                n_results=k,
            )
        except Exception as e:
            logger.error(f"Vector query failed: {e}")
            return []

        parsed = self._parse_results(results)
        logger.debug(f"Retrieved {len(parsed)} results from {collection_type}")
        return parsed

    async def retrieve_conversations(
        self,
        query: str,
        session_key: str | None = None,
        top_k: int | None = None,
    ) -> list[dict[str, Any]]:
        k = top_k or self.config.top_k

        query_embedding = await self.embedding_service.embed_single(query)

        if not query_embedding:
            return []

        where_filter = {"session_key": session_key} if session_key else None

        try:
            results = self.store.query(
                collection_name=ChromaDBStore.COLLECTION_CONVERSATION,
                query_embeddings=[query_embedding],
                n_results=k,
                where=where_filter,
            )
        except Exception as e:
            logger.error(f"Conversation query failed: {e}")
            return []

        return self._parse_results(results)

    async def retrieve_user_profile(self, user_id: str = "default") -> list[dict[str, Any]]:
        collection = self.store.get_collection(ChromaDBStore.COLLECTION_USER_PROFILE)

        try:
            results = collection.get(
                ids=[f"user_{user_id}_profile"],
                include=["documents", "metadatas"],
            )
        except Exception as e:
            logger.error(f"User profile query failed: {e}")
            return []

        items = []
        for i, doc_id in enumerate(results.get("ids", [])):
            if doc_id:
                items.append({
                    "id": doc_id,
                    "content": results["documents"][i] if i < len(results["documents"]) else "",
                    "metadata": results["metadatas"][i] if i < len(results["metadatas"]) else {},
                })

        return items

    def _parse_results(self, results: dict[str, Any]) -> list[dict[str, Any]]:
        parsed = []
        distances = results.get("distances", [[]])[0]
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        ids = results.get("ids", [[]])[0]

        for i, doc_id in enumerate(ids):
            if i < len(documents):
                parsed.append({
                    "id": doc_id,
                    "content": documents[i],
                    "metadata": metadatas[i] if i < len(metadatas) else {},
                    "distance": distances[i] if i < len(distances) else 0.0,
                })

        return parsed

    def format_memory_for_context(
        self,
        retrieved: list[dict[str, Any]],
        max_items: int = 5,
    ) -> str:
        if not retrieved:
            return ""

        items = retrieved[:max_items]
        lines = ["## Relevant Memory\n"]

        for i, item in enumerate(items, 1):
            content = item["content"]
            metadata = item["metadata"]
            timestamp = metadata.get("timestamp", "")
            role = metadata.get("role", "")
            session = metadata.get("session_key", "")

            lines.append(f"### {i}. {timestamp} [{role}] ({session})")
            lines.append(f"{content}\n")

        return "\n".join(lines)
