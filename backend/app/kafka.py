from __future__ import annotations

import json
from typing import Any, Dict, List, Optional


class KafkaPublisher:
    """Small helper around aiokafka for optional event streaming."""

    def __init__(self, bootstrap_servers: Optional[str], topic: str, enabled: bool) -> None:
        self.bootstrap_servers = bootstrap_servers
        self.topic = topic
        self.enabled = enabled and bool(bootstrap_servers)
        self._producer = None
        self.status = "disabled" if not self.enabled else "initializing"
        self.reason: Optional[str] = None
        self.events: List[Dict[str, Any]] = []

    async def startup(self) -> None:
        if not self.enabled:
            self.status = "disabled"
            return
        try:
            from aiokafka import AIOKafkaProducer
        except Exception as exc:  # pragma: no cover - import guard
            self.status = "error"
            self.reason = f"Kafka import failed: {exc}"
            self.enabled = False
            return

        self._producer = AIOKafkaProducer(
            bootstrap_servers=self.bootstrap_servers,
            value_serializer=lambda value: json.dumps(value).encode("utf-8"),
        )
        try:
            await self._producer.start()
            self.status = "ready"
        except Exception as exc:  # pragma: no cover - relies on broker
            self.status = "error"
            self.reason = str(exc)
            self._producer = None

    async def shutdown(self) -> None:
        if self._producer is not None:
            await self._producer.stop()
            self._producer = None
        if self.status == "ready":
            self.status = "stopped"

    async def emit(self, event_type: str, payload: Dict[str, Any]) -> None:
        event = {"type": event_type, "payload": payload}
        self.events.append(event)
        if self._producer is not None:
            await self._producer.send_and_wait(self.topic, event)
