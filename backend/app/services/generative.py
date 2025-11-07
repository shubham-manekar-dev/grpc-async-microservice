"""Generative healthcare insights with optional cloud providers."""

from __future__ import annotations

import asyncio
import random
from typing import Iterable, List, Optional

import httpx

from ..config import settings
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


class GenerativeCarePlanner:
    def __init__(self, provider: str, model: str, api_key: Optional[str], endpoint: Optional[str], project: Optional[str]) -> None:
        self.provider = provider.lower()
        self.model = model
        self.api_key = api_key
        self.endpoint = endpoint
        self.project = project

    async def generate(self, request: IntakeRequest) -> CarePlan:
        if self.provider in {"openai", "chatgpt"} and self.api_key:
            try:
                response = await self._call_openai(request)
                if response:
                    return response
            except Exception:  # pragma: no cover - relies on external API
                pass
        if self.provider in {"gemini", "google"} and self.api_key:
            try:
                response = await self._call_gemini(request)
                if response:
                    return response
            except Exception:  # pragma: no cover - relies on external API
                pass
        return self._heuristic_plan(request)

    async def _call_openai(self, request: IntakeRequest) -> Optional[CarePlan]:
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a clinical triage assistant generating concise care plans.",
                },
                {
                    "role": "user",
                    "content": self._format_prompt(request),
                },
            ],
            "max_tokens": 300,
            "temperature": 0.2,
        }
        headers = {"Authorization": f"Bearer {self.api_key}"}
        endpoint = self.endpoint or "https://api.openai.com/v1/chat/completions"
        async with httpx.AsyncClient(timeout=10.0) as client:
            result = await client.post(endpoint, json=payload, headers=headers)
            result.raise_for_status()
            data = result.json()
        message = data["choices"][0]["message"]["content"].strip()
        return self._care_plan_from_text(message, request)

    async def _call_gemini(self, request: IntakeRequest) -> Optional[CarePlan]:
        endpoint = self.endpoint or "https://generativelanguage.googleapis.com/v1beta/models"
        model_path = f"{endpoint}/{self.model}:generateContent"
        params = {"key": self.api_key}
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": self._format_prompt(request)},
                    ]
                }
            ]
        }
        async with httpx.AsyncClient(timeout=10.0) as client:
            result = await client.post(model_path, params=params, json=payload)
            result.raise_for_status()
            data = result.json()
        text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
        return self._care_plan_from_text(text, request)

    @staticmethod
    def _format_prompt(request: IntakeRequest) -> str:
        return (
            "Provide a triage level, bullet list of recommended diagnostics, and a short summary. "
            f"Patient symptoms: {', '.join(request.symptoms)}. "
            f"Vitals: Temp {request.vitals.temperature_c}C, HR {request.vitals.heart_rate_bpm} bpm, "
            f"BP {request.vitals.systolic_bp_mm_hg}/{request.vitals.diastolic_bp_mm_hg}."
        )

    def _care_plan_from_text(self, text: str, request: IntakeRequest) -> CarePlan:
        suggested_tests = [test.strip("- *") for test in text.splitlines() if "-" in test]
        if not suggested_tests:
            suggested_tests = self._tests_from_symptoms(request.symptoms)
        triage = "routine"
        lowered = text.lower()
        if "emerg" in lowered:
            triage = "emergency"
        elif "urgent" in lowered:
            triage = "urgent"
        return CarePlan(summary=text, suggested_tests=suggested_tests, triage_level=triage)

    @staticmethod
    def _triage_from_symptoms(symptoms: Iterable[str]) -> str:
        normalized = {symptom.lower() for symptom in symptoms}
        if TRIAGE_KEYWORDS["emergency"] & normalized:
            return "emergency"
        if TRIAGE_KEYWORDS["urgent"] & normalized:
            return "urgent"
        return "routine"

    @staticmethod
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

    def _heuristic_plan(self, request: IntakeRequest) -> CarePlan:
        triage_level = self._triage_from_symptoms(request.symptoms)
        tests = self._tests_from_symptoms(request.symptoms)
        symptom_list = ", ".join(request.symptoms) or "no symptoms reported"
        summary_templates = {
            "emergency": (
                "Symptoms of {symptoms} with heart rate {hr} bpm suggest immediate escalation. "
                "Activate emergency response, stabilize vitals, and prepare for escalation."
            ),
            "urgent": (
                "Patient reports {symptoms}. Arrange urgent clinic evaluation, provide interim "
                "guidance, and monitor trends via remote vitals."
            ),
            "routine": (
                "Presentation of {symptoms} appears stable. Reinforce preventive care, document "
                "lifestyle coaching, and schedule routine follow-up."
            ),
        }
        summary = summary_templates[triage_level].format(
            symptoms=symptom_list,
            hr=request.vitals.heart_rate_bpm,
        )
        random.seed(
            sum(ord(char) for char in symptom_list)
            + request.vitals.heart_rate_bpm
            + len(request.symptoms)
        )
        tone = random.choice(["compassionate", "confident", "reassuring"])
        summary = f"({tone} tone) {summary}"
        return CarePlan(summary=summary, suggested_tests=tests, triage_level=triage_level)


planner = GenerativeCarePlanner(
    provider=settings.gen_ai_provider,
    model=settings.gen_ai_model,
    api_key=settings.gen_ai_api_key,
    endpoint=settings.gen_ai_endpoint,
    project=settings.gen_ai_project,
)


def generate_care_plan_sync(request: IntakeRequest) -> CarePlan:
    return asyncio.get_event_loop().run_until_complete(planner.generate(request))
