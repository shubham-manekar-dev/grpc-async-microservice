from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("CARE_PLAN_GRPC_TARGET", "disabled")
os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")
os.environ.setdefault("KAFKA_ENABLED", "false")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret")
os.environ.setdefault("REDIS_URL", "memory://")
os.environ.setdefault("MONGO_URL", "memory://")

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "app") not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.database import clear_all, init_db, session_scope  # noqa: E402  pylint: disable=wrong-import-position
from app.main import app  # noqa: E402  pylint: disable=wrong-import-position


TEST_DB = ROOT / "test.db"


@pytest.fixture(scope="session", autouse=True)
def clean_database() -> None:
    if TEST_DB.exists():
        TEST_DB.unlink()
    init_db()
    yield
    if TEST_DB.exists():
        TEST_DB.unlink()


@pytest.fixture(autouse=True)
def reset_db() -> None:
    init_db()
    with session_scope() as session:
        clear_all(session)
    yield


@pytest.fixture()
def client() -> TestClient:
    with TestClient(app) as test_client:
        yield test_client
