from __future__ import annotations

from typing import Any, Dict, List, Optional

import anyio


class MongoRepository:
    """Persist intake transcripts to MongoDB with a mongomock fallback."""

    def __init__(self, url: str, database: str, collection: str) -> None:
        self.url = url
        self.database = database
        self.collection_name = collection
        self.status = "uninitialized"
        self.reason: Optional[str] = None
        self._collection = None
        self._in_memory: List[Dict[str, Any]] = []

    async def startup(self) -> None:
        if self.url.startswith("memory://"):
            self.status = "in-memory"
            self.reason = None
            self._in_memory = []
            return

        try:
            from pymongo import MongoClient  # type: ignore
        except Exception as exc:  # pragma: no cover - import guard
            self.status = "in-memory"
            self.reason = f"pymongo import failed: {exc}"
            self._collection = None
            self._in_memory = []
            return

        try:
            client = MongoClient(self.url, serverSelectionTimeoutMS=2000)
            client.server_info()
            database = client[self.database]
            self._collection = database[self.collection_name]
            self.status = "ready"
            self.reason = None
        except Exception as exc:  # pragma: no cover - network guard
            self.status = "in-memory"
            self.reason = str(exc)
            self._collection = None
            self._in_memory = []

    async def shutdown(self) -> None:
        if self.status in {"ready", "in-memory"}:
            self.status = "stopped"
        self._collection = None

    async def record_intake(self, document: Dict[str, Any]) -> None:
        self._in_memory.append(document)
        if self._collection is not None:
            await anyio.to_thread.run_sync(self._collection.insert_one, document)

    def recent_documents(self) -> List[Dict[str, Any]]:
        return list(self._in_memory)
