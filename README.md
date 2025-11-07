# Healthcare AI Experience


React microservices orchestrated with gRPC, Kafka, Postgres, MongoDB, Redis
caching, and AI-assisted care planning. The project demonstrates how to weave
secure APIs, generative intelligence, and production-grade automation together
while keeping local developer workflows identical to CI pipelines.

![Live topology demo](docs/live-topology.svg)

👉 Looking for the recruiter walk-through? Jump to the
[step-by-step user guide](docs/USER_GUIDE.md).

> 💡 The generative intake assistant can call the free ChatGPT or Gemini
> endpoints when credentials are provided. If no key is configured the service
> falls back to the deterministic heuristic generator so demos never break.

## Highlights

- **FastAPI gateway + gRPC microservice** exposed through both REST (RAML) and
  Protobuf contracts. The gateway automatically falls back to the local
  heuristics planner if gRPC is offline.
- **PostgreSQL** stores patient demographics using SQLAlchemy models, while
  **MongoDB** captures intake audit trails for downstream analytics and
  **Redis** caches patient rosters for sub-millisecond read APIs.
- **Generative AI service** optionally proxies to ChatGPT (OpenAI) or Gemini
  (Google) APIs, controlled by environment variables. A tone-aware heuristic
  fallback keeps integration tests deterministic.
- **Security** with OAuth2 password flow + JWTs, Kafka-backed event streaming,
  and Redis cache invalidation on mutations.
- **Monitoring-ready** via `/metrics` (Prometheus/Grafana), structured logs for
  Kibana, and `/integrations` surfacing gRPC/Kafka/Redis/Mongo readiness.
- **Frontend** React (Vite) console that walks recruiters through the end-to-end
  workflow, highlighting real-time AI responses.
- **Automation**: Pytest unit & integration suites, TestNG contract checks,
  minimal contract testing (MCT) of the RAML spec, Vitest for the UI, and
  ShellCheck for bash utilities—all orchestrated through `make ci` for perfect
  parity across GitHub Actions, Jenkins, and local development.

## Architecture

The stack is split into focused services:

| Component | Tech | Responsibilities |
|-----------|------|------------------|
| API Gateway | FastAPI, SQLAlchemy, Redis | REST endpoints, JWT auth, cache, orchestration |
| Care-plan service | gRPC, Protobuf | Generates AI care plans via ChatGPT/Gemini or heuristics |
| Data tier | PostgreSQL, MongoDB, Redis | Durable patient storage, audit trails, caching |
| Streaming | Kafka + Zookeeper | Emits `patient.created` and `intake.completed` events |
| Frontend | React + Vite | Recruiter-facing UI with AI demo |
| Observability | Prometheus, Grafana, Elasticsearch, Kibana | Metrics, dashboards, log exploration |

The rendered topology (`docs/live-topology.svg`) is produced by
`docs/render_topology.py`, keeping diagrams version-controlled and repeatable.
> ℹ️ The workspace PR helper refuses binary diffs, so the diagram is tracked as
> SVG. Regenerate a local PNG for slide decks with
> `python docs/render_topology.py --png`.

## Running the Stack

### Docker Compose (recommended)

```bash
docker compose up --build
```

Services exposed:

- FastAPI API: http://localhost:8000 (Swagger at `/docs`)
- React UI: http://localhost:5173
- PostgreSQL: `localhost:5432` (user `care_admin`, password `care_password`)
- MongoDB: `localhost:27017`
- Redis: `localhost:6379`
- Kafka: `localhost:9092`
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000 (admin/admin)
- Kibana: http://localhost:5601

Stop the environment with `docker compose down` and inspect logs via
`docker compose logs -f`. Makefile shorthands (`make docker-up`, `make
docker-down`, `make docker-logs`) mirror these commands.

### Manual backend setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

The backend reads these environment variables:

| Variable | Purpose | Default |
|----------|---------|---------|
| `DATABASE_URL` | SQLAlchemy connection string | `postgresql+psycopg2://care_admin:care_password@localhost:5432/care_records` |
| `MONGO_URL`, `MONGO_DB`, `MONGO_COLLECTION` | MongoDB audit store | `mongodb://localhost:27017`, `care_intelligence`, `intake_audit` |
| `REDIS_URL`, `REDIS_TTL_SECONDS` | Cache backing store | `redis://localhost:6379/0`, `60` |
| `CARE_PLAN_GRPC_TARGET` | Optional remote gRPC endpoint | `localhost:50051` (set to `disabled` to force fallback) |
| `GEN_AI_PROVIDER`, `GEN_AI_MODEL`, `GEN_AI_API_KEY`, `GEN_AI_ENDPOINT` | ChatGPT/Gemini configuration | `heuristic`, `gpt-4o-mini`, unset |
| `KAFKA_BOOTSTRAP_SERVERS`, `KAFKA_TOPIC`, `KAFKA_ENABLED` | Event streaming | disabled by default |
| `JWT_SECRET_KEY`, `JWT_ACCESS_TOKEN_EXP_MINUTES` | Security settings | demo defaults |

> The Python image bundled with this repository includes a lightweight SQLite
> compatibility layer for automated tests. Install `sqlalchemy`, `psycopg2-binary`,
> `redis`, and `pymongo` to point the gateway at real infrastructure.

To run the gRPC microservice separately:

```bash
python scripts/codegen_grpc.py
python -m app.grpc_server
```

### Manual frontend setup

```bash
cd frontend
npm install
npm run dev
```

Set `VITE_API_BASE_URL` to point the UI to a remote API instance when required.

## Generative AI configuration

1. **ChatGPT (OpenAI)**: export `GEN_AI_PROVIDER=openai` and a free API key via
   `GEN_AI_API_KEY`. Optionally override `GEN_AI_ENDPOINT`.
2. **Gemini**: export `GEN_AI_PROVIDER=gemini`, `GEN_AI_MODEL=gemini-pro`, and
   `GEN_AI_API_KEY` (or configure `GEN_AI_PROJECT` if using Google Cloud).
3. **Offline fallback**: leave keys unset to use the deterministic heuristic
   engine—ideal for CI and offline demos.

The gRPC server and FastAPI gateway both use the same planner module, so once the
provider is configured, both channels produce consistent results.

## Testing & Automation

Local developers and CI runners execute the exact same suite:

```bash
make ci             # mirrors GitHub Actions and Jenkins
make backend-test   # pytest unit tests
make integration-test  # pytest integration slice
make frontend-test  # vite build + vitest
make java-test      # Maven + TestNG RAML contract checks
make mct            # lightweight RAML contract validation (MCT)
make shellcheck     # lint shell utilities
make smoke          # curl-based API smoke test (requires a running backend)
```

Additional helpers:

- `make grpc-codegen` regenerates protobuf stubs.
- `make topology` refreshes the architecture SVG (pass `--png` for a local image).

### GitHub Actions

`.github/workflows/ci.yml` installs Python, Node.js, and Java, regenerates
protobuf assets, and runs `make ci`. The workflow automatically exercises
Pytest (unit & integration), TestNG, Vitest, ShellCheck, the RAML contract test
script, and the curl smoke test.

> If your CI runners lack outbound internet access, provide cached Maven and pip
> repositories so the TestNG suite and optional database adapters can resolve
> their dependencies.

### Jenkins

`Jenkinsfile` mirrors the same steps: checkout → Python setup → Node setup →
`make ci`. Point the pipeline at any branch to reproduce the GitHub checks.

## Monitoring & Logging

- `/metrics` exposes Prometheus counters (`patients_created_total`,
  `intake_completed_total`). Prometheus + Grafana services in Compose ingest the
  endpoint automatically.
- `/integrations` returns health for gRPC, Kafka, Redis, and Mongo, ideal for
  Grafana panels or alerting hooks.
- FastAPI logs render JSON-friendly messages suitable for shipping to
  Elasticsearch/Kibana (included in Compose for exploration).

## Security Notes

- JWT-protected patient creation and intake endpoints require tokens issued by
  `/auth/token` (demo credentials `care-admin` / `admin123`).
- Redis-backed caching invalidates on writes so stale patient lists never leak.
- Kafka publishes audit-friendly events that downstream services can consume for
  compliance tracking.

## Project Assets

- [`docs/healthcare-api.raml`](docs/healthcare-api.raml) – RAML contract.
- [`docs/render_topology.py`](docs/render_topology.py) – reproducible diagram
  generator (emits `docs/live-topology.svg` and optional PNG via `--png`).
- [`scripts/mct.py`](scripts/mct.py) – minimal contract test harness.
- [`scripts/ci_smoke.sh`](scripts/ci_smoke.sh) – curl-based smoke check.
- [`java-tests`](java-tests) – TestNG contract validation suite.

## React UI preview

Run `npm run dev` (or let Docker Compose boot the frontend) and navigate to
http://localhost:5173 to try the recruiter-ready experience. The UI calls the
FastAPI endpoints documented above and surfaces the generated care plans in
real-time.
