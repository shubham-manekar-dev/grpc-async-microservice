from __future__ import annotations

from typing import Any, Dict, List

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
try:  # pragma: no cover - optional dependency
    from sqlalchemy.orm import Session
except Exception:  # pragma: no cover - fallback for test environments without SQLAlchemy
    Session = Any  # type: ignore

from .cache import CacheClient
from .config import settings
from .database import (
    PatientRecord,
    get_patient,
    get_session,
    init_db,
    insert_patient,
    list_patients,
)
from .grpc_client import CarePlanGrpcClient
from .kafka import KafkaPublisher
from .models import CarePlan, IntakeRequest, IntakeResponse, Patient, PatientCreate
from .mongo import MongoRepository
from .security import LoginRequest, Token, User, get_current_user, login_for_access_token


app = FastAPI(title="Healthcare AI POC", version="0.4.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

care_plan_client = CarePlanGrpcClient(settings.care_plan_grpc_target)
app.state.care_plan_client = care_plan_client

kafka_publisher = KafkaPublisher(
    bootstrap_servers=settings.kafka_bootstrap_servers,
    topic=settings.kafka_topic,
    enabled=settings.kafka_enabled,
)
app.state.kafka_publisher = kafka_publisher

cache_client = CacheClient(settings.redis_url, settings.redis_ttl_seconds)
app.state.cache = cache_client

mongo_repo = MongoRepository(settings.mongo_url, settings.mongo_db, settings.mongo_collection)
app.state.mongo_repo = mongo_repo

_metrics = {
    "patients_created_total": 0,
    "intake_completed_total": 0,
}


@app.on_event("startup")
async def startup_event() -> None:
    init_db()
    await care_plan_client.startup()
    await kafka_publisher.startup()
    await cache_client.startup()
    await mongo_repo.startup()


@app.on_event("shutdown")
async def shutdown_event() -> None:
    await care_plan_client.shutdown()
    await kafka_publisher.shutdown()
    await cache_client.shutdown()
    await mongo_repo.shutdown()


@app.get("/health", tags=["system"])
def health_check() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/metrics", tags=["system"], response_class=PlainTextResponse)
def metrics() -> str:
    lines = [
        f"patients_created_total {_metrics['patients_created_total']}",
        f"intake_completed_total {_metrics['intake_completed_total']}",
    ]
    return "\n".join(lines) + "\n"


@app.get("/integrations", tags=["system"])
def integration_status() -> Dict[str, Dict[str, str]]:
    client: CarePlanGrpcClient = app.state.care_plan_client
    kafka: KafkaPublisher = app.state.kafka_publisher
    cache: CacheClient = app.state.cache
    mongo: MongoRepository = app.state.mongo_repo
    payload = {
        "care_plan_grpc": {"status": client.status},
        "event_stream": {"status": kafka.status},
        "cache": {"status": cache.status},
        "mongo": {"status": mongo.status},
    }
    if client.reason:
        payload["care_plan_grpc"]["reason"] = client.reason
    if kafka.reason:
        payload["event_stream"]["reason"] = kafka.reason
    if cache.reason:
        payload["cache"]["reason"] = cache.reason
    if mongo.reason:
        payload["mongo"]["reason"] = mongo.reason
    return payload


@app.post("/auth/token", response_model=Token, tags=["auth"])
async def issue_token(payload: LoginRequest) -> Token:
    return login_for_access_token(payload)


@app.get("/patients", response_model=List[Patient], tags=["patients"])
async def list_patients_endpoint(session: Session = Depends(get_session)) -> List[Patient]:
    cached = await cache_client.get_json("patients:list")
    if cached:
        return [Patient(**item) for item in cached]
    patients: List[Patient] = []
    for record in list_patients(session):
        patients.append(
            Patient(
                id=record.id,
                name=record.name,
                date_of_birth=record.date_of_birth,
                allergies=record.allergies,
                active_conditions=record.active_conditions,
            )
        )
    await cache_client.set_json("patients:list", [patient.model_dump(mode="json") for patient in patients])
    return patients


@app.post("/patients", response_model=Patient, status_code=201, tags=["patients"])
async def create_patient(
    patient: PatientCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> Patient:
    _ = current_user
    record = PatientRecord(
        id=0,
        name=patient.name,
        date_of_birth=patient.date_of_birth,
        allergies=patient.allergies or [],
        active_conditions=patient.active_conditions or [],
    )
    saved = insert_patient(session, record)
    response = Patient(
        id=saved.id,
        name=saved.name,
        date_of_birth=saved.date_of_birth,
        allergies=saved.allergies,
        active_conditions=saved.active_conditions,
    )
    await cache_client.delete("patients:list")
    await app.state.kafka_publisher.emit(
        "patient.created",
        {"patient_id": response.id, "name": response.name},
    )
    _metrics["patients_created_total"] += 1
    return response


@app.post("/intake/{patient_id}", response_model=IntakeResponse, tags=["intake"])
async def run_intake(
    patient_id: int,
    request: IntakeRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> IntakeResponse:
    _ = current_user
    record = get_patient(session, patient_id)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")

    patient = Patient(
        id=record.id,
        name=record.name,
        date_of_birth=record.date_of_birth,
        allergies=record.allergies,
        active_conditions=record.active_conditions,
    )
    care_plan: CarePlan = await care_plan_client.generate(request)
    response = IntakeResponse(patient=patient, care_plan=care_plan)
    await app.state.kafka_publisher.emit(
        "intake.completed",
        {
            "patient_id": patient.id,
            "triage_level": care_plan.triage_level,
        },
    )
    await mongo_repo.record_intake(
        {
            "patient_id": patient.id,
            "symptoms": request.symptoms,
            "triage_level": care_plan.triage_level,
            "summary": care_plan.summary,
        }
    )
    _metrics["intake_completed_total"] += 1
    return response
