from __future__ import annotations

import asyncio
from datetime import date

import pytest
from fastapi.testclient import TestClient

from app.models import IntakeRequest, PatientCreate, VitalSigns


def get_token(client: TestClient) -> str:
    response = client.post(
        "/auth/token",
        json={"username": "care-admin", "password": "admin123"},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def test_health_endpoint_returns_ok(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_integration_status_reports_grpc(client: TestClient) -> None:
    response = client.get("/integrations")
    payload = response.json()
    assert "care_plan_grpc" in payload
    assert payload["care_plan_grpc"]["status"] in {"disabled", "ready", "stopped", "uninitialized"}
    assert payload["cache"]["status"] in {"in-memory", "ready", "disabled", "error", "stopped"}
    assert payload["mongo"]["status"] in {"in-memory", "ready", "disabled", "error", "stopped"}


def test_create_patient_and_list(client: TestClient) -> None:
    token = get_token(client)
    payload = PatientCreate(
        name="Jamie Doe",
        date_of_birth=date(1990, 5, 4),
        allergies=["Peanuts"],
        active_conditions=["Diabetes"],
    )
    response = client.post(
        "/patients",
        json=payload.model_dump(mode="json"),
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    created = response.json()

    list_response = client.get("/patients")
    patients = list_response.json()
    assert any(patient["id"] == created["id"] for patient in patients)

    cached_value = asyncio.run(client.app.state.cache.get_json("patients:list"))
    assert cached_value is not None
    assert any(item["id"] == created["id"] for item in cached_value)

    events = client.app.state.kafka_publisher.events
    assert any(event["type"] == "patient.created" for event in events)


@pytest.mark.integration
def test_run_intake_generates_care_plan(client: TestClient) -> None:
    token = get_token(client)
    create_response = client.post(
        "/patients",
        json=PatientCreate(
            name="River Tam",
            date_of_birth=date(1989, 1, 1),
        ).model_dump(mode="json"),
        headers={"Authorization": f"Bearer {token}"},
    )
    patient_id = create_response.json()["id"]

    request = IntakeRequest(
        symptoms=["chest pain", "shortness of breath"],
        vitals=VitalSigns(
            temperature_c=37.2,
            heart_rate_bpm=110,
            systolic_bp_mm_hg=130,
            diastolic_bp_mm_hg=85,
        ),
    )

    response = client.post(
        f"/intake/{patient_id}",
        json=request.model_dump(mode="json"),
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    payload = response.json()

    assert payload["care_plan"]["triage_level"] == "emergency"
    assert any("Chest X-ray" in test for test in payload["care_plan"]["suggested_tests"])
    assert payload["care_plan"]["summary"].startswith("(")

    events = client.app.state.kafka_publisher.events
    assert any(event["type"] == "intake.completed" for event in events)

    mongo_docs = client.app.state.mongo_repo.recent_documents()
    assert any(doc["patient_id"] == patient_id for doc in mongo_docs)


def test_protected_endpoints_require_authentication(client: TestClient) -> None:
    response = client.post(
        "/patients",
        json=PatientCreate(
            name="Unauthorized User",
            date_of_birth=date(1995, 6, 6),
        ).model_dump(mode="json"),
    )
    assert response.status_code == 401
