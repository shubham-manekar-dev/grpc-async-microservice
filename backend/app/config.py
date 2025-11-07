from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class Settings:
    """Runtime configuration for the FastAPI gateway and gRPC worker."""

    care_plan_grpc_target: str = os.getenv("CARE_PLAN_GRPC_TARGET", "localhost:50051")
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg2://care_admin:care_password@postgres:5432/care_records",
    )
    mongo_url: str = os.getenv("MONGO_URL", "mongodb://mongodb:27017")
    mongo_db: str = os.getenv("MONGO_DB", "care_intelligence")
    mongo_collection: str = os.getenv("MONGO_COLLECTION", "intake_audit")
    redis_url: str = os.getenv("REDIS_URL", "redis://redis:6379/0")
    redis_ttl_seconds: int = int(os.getenv("REDIS_TTL_SECONDS", "60"))

    jwt_secret_key: str = os.getenv("JWT_SECRET_KEY", "change-me-in-prod")
    jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
    jwt_access_token_exp_minutes: int = int(os.getenv("JWT_ACCESS_TOKEN_EXP_MINUTES", "30"))

    kafka_bootstrap_servers: Optional[str] = os.getenv("KAFKA_BOOTSTRAP_SERVERS")
    kafka_topic: str = os.getenv("KAFKA_TOPIC", "care-events")
    kafka_enabled: bool = os.getenv("KAFKA_ENABLED", "false").lower() in {"1", "true", "yes"}

    gen_ai_provider: str = os.getenv("GEN_AI_PROVIDER", "heuristic")
    gen_ai_model: str = os.getenv("GEN_AI_MODEL", "gpt-4o-mini")
    gen_ai_api_key: Optional[str] = os.getenv("GEN_AI_API_KEY")
    gen_ai_project: Optional[str] = os.getenv("GEN_AI_PROJECT")
    gen_ai_endpoint: Optional[str] = os.getenv("GEN_AI_ENDPOINT")


settings = Settings()
