# Healthcare AI POC

This repository hosts a proof-of-concept healthcare triage platform. The project
pairs a FastAPI backend with a React (Vite) frontend to demonstrate how a
clinical intake workflow can be enhanced with a lightweight generative AI
experience.

## Features

- **FastAPI backend** with endpoints for health checks, patient management, and
  an AI-assisted intake workflow.
- **Generative care plan service** that produces triage guidance and suggested
  diagnostics using symptom heuristics and templated narratives.
- **React UI** (Material UI + Vite) for browsing patients and launching the AI
  intake assistant.
- **RAML contract** (`docs/healthcare-api.raml`) describing the public API.
- **Automated testing** via `pytest` for the backend and `vitest` for the
  frontend.
- **GitHub Actions CI** workflow that installs dependencies and executes the
  full test suite on every push and pull request.

## Getting Started

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Set the backend URL with `VITE_API_BASE_URL` (defaults to `http://localhost:8000`).

### Testing

```bash
cd backend
pytest

cd ../frontend
npm test -- --run
```

## API Contract

The REST contract is captured in [`docs/healthcare-api.raml`](docs/healthcare-api.raml).
Use tools such as [API Workbench](https://apiworkbench.com/) or
[ramlfications](https://github.com/spotify/ramlfications) to explore the
specification.
