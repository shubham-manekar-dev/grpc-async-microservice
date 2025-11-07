from __future__ import annotations

import logging
from typing import Optional

from .models import CarePlan, IntakeRequest
from .proto import runtime as proto_runtime
from .services.generative import planner

LOGGER = logging.getLogger(__name__)


class CarePlanGrpcClient:
    """Lazy gRPC client that gracefully falls back to local generation."""

    def __init__(self, target: str) -> None:
        self._target = target
        self._channel = None
        self._stub = None
        self._pb2 = None
        self.status: str = "uninitialized"
        self.reason: Optional[str] = None

    async def startup(self) -> None:
        if self._target in {"", "disabled"}:
            self.status = "disabled"
            self.reason = "Disabled via configuration"
            LOGGER.info("gRPC client disabled via configuration")
            return
        if not proto_runtime.grpc_available():
            self.status = "disabled"
            self.reason = proto_runtime.grpc_unavailable_reason()
            LOGGER.info("gRPC client disabled: %s", self.reason)
            return

        import grpc  # type: ignore

        self.status = "starting"
        pb2, pb2_grpc = proto_runtime.grpc_modules()  # type: ignore[assignment]
        if pb2 is None or pb2_grpc is None:
            self.status = "disabled"
            self.reason = proto_runtime.grpc_unavailable_reason()
            LOGGER.info("gRPC modules unavailable: %s", self.reason)
            return

        self._pb2 = pb2
        self._channel = grpc.aio.insecure_channel(self._target)
        self._stub = pb2_grpc.CarePlanGeneratorStub(self._channel)
        self.status = "ready"
        self.reason = None
        LOGGER.info("Connected to care-plan gRPC service at %s", self._target)

    async def shutdown(self) -> None:
        if self._channel is not None:
            await self._channel.close()
        self._channel = None
        self._stub = None
        self._pb2 = None
        if self.status == "ready":
            self.status = "stopped"

    async def generate(self, request: IntakeRequest) -> CarePlan:
        if self._stub is None or self._pb2 is None:
            if self.status == "ready":
                LOGGER.warning("gRPC stub missing despite ready status; falling back")
            return await planner.generate(request)

        import grpc  # type: ignore

        try:
            proto_request = proto_runtime.to_proto_request(self._pb2, request)
            response = await self._stub.GenerateCarePlan(proto_request)
            return proto_runtime.from_proto_response(response)
        except grpc.RpcError as exc:  # type: ignore[attr-defined]
            self.status = "error"
            self.reason = f"gRPC invocation failed: {exc}"  # pragma: no cover - diagnostic path
            LOGGER.exception("gRPC call failed, using local fallback")
            return await planner.generate(request)
