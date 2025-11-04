from __future__ import annotations

from datetime import date

from fastapi.testclient import TestClient

from app.main import app
from app.models import IntakeRequest, PatientCreate, VitalSigns


client = TestClient(app)


def test_health_endpoint_returns_ok() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_create_patient_and_list() -> None:
    payload = PatientCreate(
        name="Jamie Doe",
        date_of_birth=date(1990, 5, 4),
        allergies=["Peanuts"],
        active_conditions=["Diabetes"],
    )
    response = client.post("/patients", json=payload.model_dump(mode="json"))
    assert response.status_code == 201
    created = response.json()

    list_response = client.get("/patients")
    patients = list_response.json()
    assert any(patient["id"] == created["id"] for patient in patients)


def test_run_intake_generates_care_plan() -> None:
    request = IntakeRequest(
        symptoms=["chest pain", "shortness of breath"],
        vitals=VitalSigns(
            temperature_c=37.2,
            heart_rate_bpm=110,
            systolic_bp_mm_hg=130,
            diastolic_bp_mm_hg=85,
        ),
    )

    response = client.post("/intake/1", json=request.model_dump(mode="json"))
    assert response.status_code == 200
    payload = response.json()

    assert payload["care_plan"]["triage_level"] == "emergency"
    assert any("Chest X-ray" in test for test in payload["care_plan"]["suggested_tests"])
    assert payload["care_plan"]["summary"].startswith("(")
