"""ChromaDB store for vector memory."""

import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from loguru import logger

from nanobot.agent.vector_memory.config import get_config


class ChromaDBStore:
    COLLECTION_USER_PROFILE = "user_profile"
    COLLECTION_CONVERSATION = "conversation"

    def __init__(self, persist_directory: Path | None = None):
        import chromadb
        from chromadb.config import Settings

        config = get_config()
        self.persist_dir = persist_directory or config.get_persist_dir()
        self.persist_dir.mkdir(parents=True, exist_ok=True)

        self.client = chromadb.PersistentClient(
            path=str(self.persist_dir),
            settings=Settings(anonymized_telemetry=False),
        )

        self._ensure_collections()

    def _ensure_collections(self) -> None:
        try:
            self.client.get_collection(name=self.COLLECTION_USER_PROFILE)
        except Exception:
            self.client.create_collection(
                name=self.COLLECTION_USER_PROFILE,
                metadata={"description": "User profile memory store"},
            )

        try:
            self.client.get_collection(name=self.COLLECTION_CONVERSATION)
        except Exception:
            self.client.create_collection(
                name=self.COLLECTION_CONVERSATION,
                metadata={"description": "Conversation history store"},
            )

    def get_collection(self, name: str):
        return self.client.get_collection(name=name)

    def add_user_profile(
        self,
        user_id: str,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        collection = self.get_collection(self.COLLECTION_USER_PROFILE)
        doc_id = f"user_{user_id}_profile"

        existing = collection.get(ids=[doc_id])
        if existing and existing["ids"]:
            collection.update(
                ids=[doc_id],
                documents=[content],
                metadatas=[metadata or {}],
            )
        else:
            collection.add(
                ids=[doc_id],
                documents=[content],
                metadatas=[metadata or {}],
            )

        logger.debug(f"Added/updated user profile: {doc_id}")
        return doc_id

    def add_conversation(
        self,
        session_key: str,
        role: str,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        collection = self.get_collection(self.COLLECTION_CONVERSATION)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        doc_id = f"{session_key}_{timestamp}_{uuid.uuid4().hex[:8]}"

        meta = metadata or {}
        meta["session_key"] = session_key
        meta["role"] = role
        meta["timestamp"] = datetime.now().isoformat()

        collection.add(
            ids=[doc_id],
            documents=[content],
            metadatas=[meta],
        )

        logger.debug(f"Added conversation: {doc_id}")
        return doc_id

    def query(
        self,
        collection_name: str,
        query_embeddings: list[list[float]],
        n_results: int = 5,
        where: dict[str, Any] | None = None,
        where_document: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        collection = self.get_collection(collection_name)

        results = collection.query(
            query_embeddings=query_embeddings,
            n_results=n_results,
            where=where,
            where_document=where_document,
        )

        return results

    def get_recent_conversations(
        self,
        session_key: str | None = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        collection = self.get_collection(self.COLLECTION_CONVERSATION)

        where_filter = {"session_key": session_key} if session_key else None

        results = collection.get(
            where=where_filter,
            limit=limit,
            include=["documents", "metadatas"],
        )

        items = []
        for i, doc_id in enumerate(results.get("ids", [])):
            items.append({
                "id": doc_id,
                "content": results["documents"][i] if i < len(results["documents"]) else "",
                "metadata": results["metadatas"][i] if i < len(results["metadatas"]) else {},
            })

        items.sort(key=lambda x: x["metadata"].get("timestamp", ""), reverse=True)
        return items

    def count(self, collection_name: str) -> int:
        collection = self.get_collection(collection_name)
        return collection.count()

    def delete_collection(self, name: str) -> None:
        self.client.delete_collection(name=name)
        logger.info(f"Deleted collection: {name}")
