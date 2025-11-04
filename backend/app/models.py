from __future__ import annotations

from datetime import date
from typing import List, Optional

from pydantic import BaseModel, Field


class VitalSigns(BaseModel):
    temperature_c: float = Field(..., ge=30, le=45)
    heart_rate_bpm: int = Field(..., ge=30, le=240)
    systolic_bp_mm_hg: int = Field(..., ge=50, le=250)
    diastolic_bp_mm_hg: int = Field(..., ge=30, le=200)


class Patient(BaseModel):
    id: int = Field(..., ge=1)
    name: str = Field(..., min_length=1)
    date_of_birth: date
    allergies: List[str] = []
    active_conditions: List[str] = []


class PatientCreate(BaseModel):
    name: str = Field(..., min_length=1)
    date_of_birth: date
    allergies: Optional[List[str]] = None
    active_conditions: Optional[List[str]] = None


class IntakeRequest(BaseModel):
    symptoms: List[str]
    vitals: VitalSigns


class CarePlan(BaseModel):
    summary: str
    suggested_tests: List[str]
    triage_level: str


class IntakeResponse(BaseModel):
    patient: Patient
    care_plan: CarePlan
