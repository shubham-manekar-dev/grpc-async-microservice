from __future__ import annotations

import json
from typing import Any, Optional


class _DictCache:
    def __init__(self) -> None:
        self.store: dict[str, str] = {}

    async def get(self, key: str) -> Optional[str]:
        return self.store.get(key)

    async def set(self, key: str, value: str, ex: Optional[int] = None) -> None:  # noqa: ARG002 - ttl unused
        self.store[key] = value

    async def delete(self, key: str) -> None:
        self.store.pop(key, None)

    async def close(self) -> None:
        self.store.clear()


class CacheClient:
    """Thin wrapper around Redis with an in-memory fallback for tests."""

    def __init__(self, url: str, default_ttl: int) -> None:
        self.url = url
        self.default_ttl = default_ttl
        self._client: Optional[Any] = None
        self.status = "uninitialized"
        self.reason: Optional[str] = None

    async def startup(self) -> None:
        if self.url.startswith("memory://"):
            self._client = _DictCache()
            self.status = "in-memory"
            self.reason = None
            return

        try:
            from redis.asyncio import from_url  # type: ignore
        except Exception as exc:  # pragma: no cover - import guard
            self._client = _DictCache()
            self.status = "in-memory"
            self.reason = f"redis import failed: {exc}"
            return

        try:
            self._client = from_url(self.url, encoding="utf-8", decode_responses=True)
            await self._client.ping()
            self.status = "ready"
            self.reason = None
        except Exception as exc:  # pragma: no cover - network guard
            self._client = _DictCache()
            self.status = "in-memory"
            self.reason = str(exc)

    async def shutdown(self) -> None:
        if self._client is not None:
            await self._client.close()
        self._client = None
        if self.status in {"ready", "in-memory"}:
            self.status = "stopped"

    async def get_json(self, key: str) -> Optional[Any]:
        if self._client is None:
            return None
        raw = await self._client.get(key)
        if raw is None:
            return None
        return json.loads(raw)

    async def set_json(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        if self._client is None:
            return
        payload = json.dumps(value)
        await self._client.set(key, payload, ex=ttl or self.default_ttl)

    async def delete(self, key: str) -> None:
        if self._client is None:
            return
        await self._client.delete(key)
