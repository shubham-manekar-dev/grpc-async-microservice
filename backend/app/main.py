from __future__ import annotations

from datetime import date
from typing import Dict, List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .models import CarePlan, IntakeRequest, IntakeResponse, Patient, PatientCreate
from .services.generative import generate_care_plan


app = FastAPI(title="Healthcare AI POC", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# In-memory patient registry for the proof of concept.
PATIENTS: Dict[int, Patient] = {
    1: Patient(
        id=1,
        name="Avery Johnson",
        date_of_birth=date(1985, 3, 17),
        allergies=["Penicillin"],
        active_conditions=["Hypertension"],
    )
}


def _next_patient_id() -> int:
    return max(PATIENTS) + 1 if PATIENTS else 1


@app.get("/health", tags=["system"])
def health_check() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/patients", response_model=List[Patient], tags=["patients"])
def list_patients() -> List[Patient]:
    return list(PATIENTS.values())


@app.post("/patients", response_model=Patient, status_code=201, tags=["patients"])
def create_patient(patient: PatientCreate) -> Patient:
    new_id = _next_patient_id()
    patient_record = Patient(
        id=new_id,
        name=patient.name,
        date_of_birth=patient.date_of_birth,
        allergies=patient.allergies or [],
        active_conditions=patient.active_conditions or [],
    )
    PATIENTS[new_id] = patient_record
    return patient_record


@app.post("/intake/{patient_id}", response_model=IntakeResponse, tags=["intake"])
def run_intake(patient_id: int, request: IntakeRequest) -> IntakeResponse:
    if patient_id not in PATIENTS:
        raise HTTPException(status_code=404, detail="Patient not found")

    patient = PATIENTS[patient_id]
    care_plan: CarePlan = generate_care_plan(request)
    return IntakeResponse(patient=patient, care_plan=care_plan)
