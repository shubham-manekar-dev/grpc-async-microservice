from __future__ import annotations

import asyncio
import logging
from typing import Optional

from .models import IntakeRequest, VitalSigns
from .proto import runtime as proto_runtime
from .services.generative import planner

LOGGER = logging.getLogger(__name__)


def _ensure_runtime() -> tuple:
    if not proto_runtime.grpc_available():
        reason = proto_runtime.grpc_unavailable_reason()
        raise RuntimeError(
            "gRPC runtime is not available. "
            "Install grpcio/grpcio-tools and generate stubs before starting the server.\n"
            f"Reason: {reason}"
        )

    import grpc  # type: ignore

    pb2, pb2_grpc = proto_runtime.grpc_modules()  # type: ignore[assignment]
    if pb2 is None or pb2_grpc is None:
        raise RuntimeError("Failed to load protobuf modules after availability check.")
    return grpc, pb2, pb2_grpc


class CarePlanGeneratorService:
    """Async gRPC service for the care-plan generator."""

    def __init__(self, pb2) -> None:  # type: ignore[no-untyped-def]
        self._pb2 = pb2

    async def GenerateCarePlan(self, request, context):  # type: ignore[no-untyped-def]
        domain_request = IntakeRequest(
            symptoms=list(request.symptoms),
            vitals=VitalSigns(
                temperature_c=request.vitals.temperature_c,
                heart_rate_bpm=request.vitals.heart_rate_bpm,
                systolic_bp_mm_hg=request.vitals.systolic_bp_mm_hg,
                diastolic_bp_mm_hg=request.vitals.diastolic_bp_mm_hg,
            ),
        )
        plan = await planner.generate(domain_request)
        return self._pb2.CarePlan(  # type: ignore[attr-defined]
            summary=plan.summary,
            suggested_tests=list(plan.suggested_tests),
            triage_level=plan.triage_level,
        )


async def serve(bind: str = "0.0.0.0:50051") -> None:
    grpc, pb2, pb2_grpc = _ensure_runtime()

    server = grpc.aio.server()
    pb2_grpc.add_CarePlanGeneratorServicer_to_server(  # type: ignore[attr-defined]
        CarePlanGeneratorService(pb2),
        server,
    )
    server.add_insecure_port(bind)
    LOGGER.info("Starting care-plan gRPC server on %s", bind)
    await server.start()
    await server.wait_for_termination()


def main(bind: Optional[str] = None) -> None:
    bind_target = bind or "0.0.0.0:50051"
    asyncio.run(serve(bind_target))


if __name__ == "__main__":
    main()
