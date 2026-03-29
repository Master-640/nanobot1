"""Embedding service for vector memory using DeepSeek embedding API."""

import os
import httpx
from typing import Any

from nanobot.agent.vector_memory.config import get_config


class EmbeddingService:
    def __init__(self, api_key: str | None = None, api_base: str | None = None):
        config = get_config()
        self.api_key = api_key or os.environ.get("DEEPSEEK_API_KEY", "")
        self.api_base = api_base or "https://api.deepseek.com"
        self.model = config.embedding_model
        self.dimension = config.embedding_dimension

    async def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        url = f"{self.api_base}/embeddings"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        data = {
            "model": self.model,
            "input": texts,
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=data, headers=headers)
            response.raise_for_status()
            result = response.json()

        embeddings = [item["embedding"] for item in result["data"]]
        return embeddings

    async def embed_single(self, text: str) -> list[float]:
        embeddings = await self.embed([text])
        return embeddings[0] if embeddings else []
