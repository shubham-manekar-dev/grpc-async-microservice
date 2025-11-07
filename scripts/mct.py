#!/usr/bin/env python3
"""Minimal contract tests for the RAML specification."""

from __future__ import annotations

from pathlib import Path
import sys


REQUIRED_SNIPPETS = [
    "title: Healthcare Intake API",
    "/patients:",
    "get:",
    "post:",
    "/intake/{patient_id}:",
    "description: Run the AI-enabled intake flow for a patient.",
]


def main() -> int:
    contract_path = Path("docs/healthcare-api.raml")
    if not contract_path.exists():
        print("RAML contract not found", file=sys.stderr)
        return 1
    content = contract_path.read_text(encoding="utf-8")
    missing = [snippet for snippet in REQUIRED_SNIPPETS if snippet not in content]
    if missing:
        print("Contract validation failed; missing snippets:\n" + "\n".join(missing), file=sys.stderr)
        return 1
    print("RAML contract includes required resources and descriptions.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
