# User Guide

This guide walks through the full recruiter demo experience: provisioning the
stack, running automated tests, exploring the APIs, and validating the
generative AI workflow. Start by opening [`docs/workflow.apng`](workflow.apng)
to see the animated journey recruiters watch during the live walkthrough.

## 0. Clone the repository

```bash
git clone https://github.com/shubham-manekar-dev/grpc-async-microservice.git
cd grpc-async-microservice
git checkout create-mini-projet-with-demo
```

The feature branch keeps the folder structure rooted under a `POC/` prefix so
your local paths mirror the recruiter screenshots and CI logs (`POC/create-mini-project-with-demo-zizq9h`).

## 1. Prerequisites

Install the following tooling locally:

- Docker Desktop 4.x (Compose v2)
- Python 3.11+
- Node.js 20+
- Java 17+ (for TestNG RAML checks)
- Make (GNU) and Bash

> **Tip:** All commands can be executed from the repository root unless noted
> otherwise.

## 2. Boot the full stack

```bash
docker compose up --build
```

Wait for the services to report healthy in the logs. The stack exposes:

| Service | URL | Notes |
|---------|-----|-------|
| FastAPI gateway | http://localhost:8000 | Swagger docs at `/docs` |
| React UI | http://localhost:5173 | Recruiter console |
| Postgres | `localhost:5432` | Credentials `care_admin` / `care_password` |
| MongoDB | `localhost:27017` | Used for intake audits |
| Redis | `localhost:6379` | Cache for patient rosters |
| Kafka | `localhost:9092` | Publishes `patient.created` events |
| Prometheus | http://localhost:9090 | Scrapes `/metrics` |
| Grafana | http://localhost:3000 | Default credentials `admin` / `admin` |
| Kibana | http://localhost:5601 | Search FastAPI JSON logs |

Shut the environment down with:

```bash
docker compose down
```

## 3. Configure generative AI (optional)

Export credentials before booting the stack to use the live providers:

```bash
# ChatGPT free tier
export GEN_AI_PROVIDER=openai
export GEN_AI_API_KEY="sk-..."
export GEN_AI_MODEL=gpt-4o-mini

# Gemini free tier
export GEN_AI_PROVIDER=gemini
export GEN_AI_API_KEY="your-gemini-key"
export GEN_AI_MODEL=gemini-pro
```

If no keys are provided, the deterministic heuristic planner runs so the demo
remains functional offline.

## 4. Obtain a JWT token

Use the demo credentials to authenticate:

```bash
curl -X POST http://localhost:8000/auth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=care-admin&password=admin123"
```

The response contains `access_token`. Store it in a shell variable for later
commands:

```bash
export ACCESS_TOKEN=$(curl -s -X POST http://localhost:8000/auth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=care-admin&password=admin123" | jq -r '.access_token')
```

## 5. Exercise the API

Create a patient (writes to Postgres/Mongo, invalidates Redis, emits Kafka):

```bash
curl -X POST http://localhost:8000/patients \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
        "first_name": "Avery",
        "last_name": "Harper",
        "date_of_birth": "1989-01-04",
        "conditions": ["hypertension"]
      }'
```

Fetch the roster (served from Redis after the first request):

```bash
curl http://localhost:8000/patients
```

Trigger an intake (persists audit trail, requests AI care plan):

```bash
curl -X POST http://localhost:8000/intake \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
        "patient_id": 1,
        "symptoms": ["shortness of breath"],
        "tone": "reassuring"
      }'
```

## 6. Verify supporting systems

- **Kafka:** `docker compose exec kafka kafka-console-consumer --topic care-events --from-beginning --bootstrap-server localhost:9092`
- **MongoDB:** `docker compose exec mongo mongosh --eval 'db.intake_audit.find().pretty()'`
- **Redis:** `docker compose exec redis redis-cli KEYS '*'`
- **Metrics:** Visit `http://localhost:8000/metrics` and confirm counters increment.
- **Integrations health:** `curl http://localhost:8000/integrations` should report `ok` statuses.

## 7. Use the React recruiter console

Navigate to http://localhost:5173 and follow the guided workflow:

1. Authenticate via the UI form (uses the same demo credentials).
2. Create or select a patient; the roster pulls from FastAPI → Redis.
3. Start an intake to view the generated care plan and Kafka confirmation.
4. Inspect the activity stream highlighting Mongo audit inserts and Kafka
   events in real time.

## 8. Automated testing (mirrors CI)

Run the full pipeline locally:

```bash
make ci
```

Individual suites:

```bash
make backend-test      # Pytest unit tests
make integration-test  # Pytest integration slice
make frontend-test     # Vite build + Vitest
make java-test         # Maven + TestNG RAML
make mct               # Python RAML contract checks
make shellcheck        # Bash linting
make smoke             # Curl smoke test (requires running FastAPI)
```

## 9. Jenkins and GitHub Actions

- GitHub Actions (`.github/workflows/ci.yml`) runs `make ci` on pushes/PRs.
- Jenkins (`Jenkinsfile`) mirrors the same stage order, guaranteeing parity
  between local, GitHub, and enterprise CI/CD.

## 10. Cleanup

- `docker compose down -v` removes containers and volumes.
- `docker system prune` frees cached images when finished evaluating the demo.

You're now ready to walk recruiters through the end-to-end healthcare AI story.
