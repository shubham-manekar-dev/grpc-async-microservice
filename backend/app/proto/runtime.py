from __future__ import annotations

import importlib
from typing import Any, Optional, Tuple

from ..models import CarePlan, IntakeRequest


_PROTO_PB2_PATH = "app.proto.generated.care_plan_pb2"
_PROTO_GRPC_PATH = "app.proto.generated.care_plan_pb2_grpc"


def _load_optional_module(path: str) -> Optional[Any]:
    spec = importlib.util.find_spec(path)
    if spec is None:
        return None
    return importlib.import_module(path)


def grpc_modules() -> Optional[Tuple[Any, Any]]:
    pb2 = _load_optional_module(_PROTO_PB2_PATH)
    pb2_grpc = _load_optional_module(_PROTO_GRPC_PATH)
    if pb2 is None or pb2_grpc is None:
        return None
    return pb2, pb2_grpc


def grpc_available() -> bool:
    grpc_spec = importlib.util.find_spec("grpc")
    if grpc_spec is None:
        return False
    return grpc_modules() is not None


def grpc_unavailable_reason() -> str:
    if importlib.util.find_spec("grpc") is None:
        return (
            "grpcio is not installed. Install optional dependencies with "
            "`pip install grpcio grpcio-tools` and regenerate the protobuf "
            "artifacts."
        )
    modules = grpc_modules()
    if modules is None:
        return (
            "Generated protobuf modules not found. Run `scripts/codegen_grpc.py` "
            "to compile `care_plan.proto` into Python classes."
        )
    return ""


def to_proto_request(pb2: Any, request: IntakeRequest) -> Any:
    vitals = pb2.VitalSigns(
        temperature_c=request.vitals.temperature_c,
        heart_rate_bpm=request.vitals.heart_rate_bpm,
        systolic_bp_mm_hg=request.vitals.systolic_bp_mm_hg,
        diastolic_bp_mm_hg=request.vitals.diastolic_bp_mm_hg,
    )
    return pb2.IntakeRequest(symptoms=list(request.symptoms), vitals=vitals)


def from_proto_response(response: Any) -> CarePlan:
    return CarePlan(
        summary=response.summary,
        suggested_tests=list(response.suggested_tests),
        triage_level=response.triage_level,
    )
