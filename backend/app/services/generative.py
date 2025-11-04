"""Simple generative healthcare insights service.

This module simulates an AI-powered triage engine by combining heuristics with
prompt-like templates. The goal is to make the proof of concept approachable
without requiring external API credentials.
"""

from __future__ import annotations

from typing import Iterable, List

import random

from ..models import CarePlan, IntakeRequest


TRIAGE_KEYWORDS = {
    "emergency": {"chest pain", "shortness of breath", "loss of consciousness"},
    "urgent": {"high fever", "severe pain", "uncontrolled bleeding"},
    "routine": {"follow-up", "refill", "mild"},
}

SUGGESTED_TESTS = {
    "cardiac": {"ECG", "Cardiac enzymes", "Chest X-ray"},
    "respiratory": {"Chest X-ray", "Pulse oximetry", "Spirometry"},
    "general": {"CBC", "Comprehensive metabolic panel", "Urinalysis"},
}


def _triage_from_symptoms(symptoms: Iterable[str]) -> str:
    normalized = {symptom.lower() for symptom in symptoms}
    if TRIAGE_KEYWORDS["emergency"] & normalized:
        return "emergency"
    if TRIAGE_KEYWORDS["urgent"] & normalized:
        return "urgent"
    return "routine"


def _tests_from_symptoms(symptoms: Iterable[str]) -> List[str]:
    normalized = " ".join(symptoms).lower()
    tests = set()
    if any(keyword in normalized for keyword in ("cough", "breath", "respiratory")):
        tests |= SUGGESTED_TESTS["respiratory"]
    if any(keyword in normalized for keyword in ("chest", "heart", "cardiac")):
        tests |= SUGGESTED_TESTS["cardiac"]
    if not tests:
        tests |= SUGGESTED_TESTS["general"]
    return sorted(tests)


def generate_care_plan(request: IntakeRequest) -> CarePlan:
    """Generate a pseudo-intelligent care plan.

    The function mixes keyword-based heuristics with narrative templates so that
    the output looks conversational while remaining deterministic for tests.
    """

    triage_level = _triage_from_symptoms(request.symptoms)
    tests = _tests_from_symptoms(request.symptoms)

    symptom_list = ", ".join(request.symptoms) or "no symptoms reported"

    summary_templates = {
        "emergency": (
            "Symptoms of {symptoms} in conjunction with vitals indicating heart rate {hr} bpm "
            "suggest immediate emergency response. Initiate ACLS protocols and prepare for "
            "advanced imaging."
        ),
        "urgent": (
            "Patient reports {symptoms}. Recommend expedited in-person assessment. Provide "
            "supportive care instructions and schedule urgent clinic visit."
        ),
        "routine": (
            "Presentation of {symptoms} appears stable. Offer remote monitoring guidance and "
            "reinforce preventive care measures."
        ),
    }

    summary = summary_templates[triage_level].format(
        symptoms=symptom_list,
        hr=request.vitals.heart_rate_bpm,
    )

    # Add a touch of variability for the POC experience while maintaining reproducibility.
    random.seed(sum(ord(char) for char in symptom_list) + request.vitals.heart_rate_bpm)
    tone = random.choice(["compassionate", "confident", "reassuring"])
    summary = f"({tone} tone) {summary}"

    return CarePlan(summary=summary, suggested_tests=tests, triage_level=triage_level)
