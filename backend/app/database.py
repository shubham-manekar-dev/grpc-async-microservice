from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from datetime import date
from typing import Generator, Iterable, List

from .config import settings

try:  # pragma: no cover - exercised in environments with SQLAlchemy installed
    from sqlalchemy import Column, Date, Integer, String, create_engine, select
    from sqlalchemy.exc import SQLAlchemyError
    from sqlalchemy.orm import Session, declarative_base, sessionmaker

    HAS_SQLALCHEMY = True
except Exception:  # pragma: no cover - offline environments
    HAS_SQLALCHEMY = False


@dataclass
class PatientRecord:
    id: int
    name: str
    date_of_birth: date
    allergies: List[str]
    active_conditions: List[str]


def serialize_list(items: List[str]) -> str:
    return ",".join(items)


def deserialize_list(raw: str) -> List[str]:
    if not raw:
        return []
    return [value for value in raw.split(",") if value]


if HAS_SQLALCHEMY:
    Base = declarative_base()

    class PatientORM(Base):  # type: ignore[no-redef]
        __tablename__ = "patients"

        id = Column(Integer, primary_key=True, index=True)
        name = Column(String, nullable=False)
        date_of_birth = Column(Date, nullable=False)
        allergies = Column(String, default="", nullable=False)
        active_conditions = Column(String, default="", nullable=False)

    def _engine_kwargs() -> dict:
        if settings.database_url.startswith("sqlite"):
            return {"connect_args": {"check_same_thread": False}}
        return {}

    ENGINE = create_engine(settings.database_url, future=True, pool_pre_ping=True, **_engine_kwargs())
    SessionLocal = sessionmaker(bind=ENGINE, expire_on_commit=False, class_=Session)

    @contextmanager
    def session_scope() -> Generator[Session, None, None]:
        session = SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def get_session() -> Iterable[Session]:
        with session_scope() as session:
            yield session

    def init_db() -> None:
        Base.metadata.create_all(bind=ENGINE)

    def list_patients(session: Session) -> List[PatientRecord]:
        results = session.execute(select(PatientORM).order_by(PatientORM.id)).scalars().all()
        return [
            PatientRecord(
                id=patient.id,
                name=patient.name,
                date_of_birth=patient.date_of_birth,
                allergies=deserialize_list(patient.allergies),
                active_conditions=deserialize_list(patient.active_conditions),
            )
            for patient in results
        ]

    def insert_patient(session: Session, record: PatientRecord) -> PatientRecord:
        patient = PatientORM(
            name=record.name,
            date_of_birth=record.date_of_birth,
            allergies=serialize_list(record.allergies),
            active_conditions=serialize_list(record.active_conditions),
        )
        session.add(patient)
        session.flush()
        return PatientRecord(
            id=patient.id,
            name=patient.name,
            date_of_birth=patient.date_of_birth,
            allergies=record.allergies,
            active_conditions=record.active_conditions,
        )

    def get_patient(session: Session, patient_id: int) -> PatientRecord | None:
        patient = session.get(PatientORM, patient_id)
        if patient is None:
            return None
        return PatientRecord(
            id=patient.id,
            name=patient.name,
            date_of_birth=patient.date_of_birth,
            allergies=deserialize_list(patient.allergies),
            active_conditions=deserialize_list(patient.active_conditions),
        )

    def clear_all(session: Session) -> None:
        try:
            session.query(PatientORM).delete()
            session.commit()
        except SQLAlchemyError:
            session.rollback()
            raise

else:  # Fallback path for environments without SQLAlchemy/psycopg2
    import sqlite3
    from pathlib import Path

    if settings.database_url.startswith("sqlite"):
        _DB_PATH = settings.database_url.replace("sqlite:///", "", 1)
    else:
        # Provide a deterministic fallback so tests work offline while README documents
        # how to enable full PostgreSQL support.
        _DB_PATH = "./data/fallback.db"
    Path(_DB_PATH).parent.mkdir(parents=True, exist_ok=True)

    def _ensure_connection() -> sqlite3.Connection:
        conn = sqlite3.connect(_DB_PATH, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    @contextmanager
    def session_scope() -> Generator[sqlite3.Connection, None, None]:
        conn = _ensure_connection()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def get_session() -> Iterable[sqlite3.Connection]:
        with session_scope() as conn:
            yield conn

    def init_db() -> None:
        with session_scope() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS patients (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    date_of_birth TEXT NOT NULL,
                    allergies TEXT DEFAULT '',
                    active_conditions TEXT DEFAULT ''
                )
                """
            )

    def list_patients(conn: sqlite3.Connection) -> List[PatientRecord]:
        rows = conn.execute(
            "SELECT id, name, date_of_birth, allergies, active_conditions FROM patients ORDER BY id"
        ).fetchall()
        return [
            PatientRecord(
                id=row["id"],
                name=row["name"],
                date_of_birth=date.fromisoformat(row["date_of_birth"]),
                allergies=deserialize_list(row["allergies"]),
                active_conditions=deserialize_list(row["active_conditions"]),
            )
            for row in rows
        ]

    def insert_patient(conn: sqlite3.Connection, record: PatientRecord) -> PatientRecord:
        cursor = conn.execute(
            "INSERT INTO patients (name, date_of_birth, allergies, active_conditions) VALUES (?, ?, ?, ?)",
            (
                record.name,
                record.date_of_birth.isoformat(),
                serialize_list(record.allergies),
                serialize_list(record.active_conditions),
            ),
        )
        new_id = cursor.lastrowid
        return PatientRecord(
            id=new_id,
            name=record.name,
            date_of_birth=record.date_of_birth,
            allergies=record.allergies,
            active_conditions=record.active_conditions,
        )

    def get_patient(conn: sqlite3.Connection, patient_id: int) -> PatientRecord | None:
        row = conn.execute(
            "SELECT id, name, date_of_birth, allergies, active_conditions FROM patients WHERE id = ?",
            (patient_id,),
        ).fetchone()
        if row is None:
            return None
        return PatientRecord(
            id=row["id"],
            name=row["name"],
            date_of_birth=date.fromisoformat(row["date_of_birth"]),
            allergies=deserialize_list(row["allergies"]),
            active_conditions=deserialize_list(row["active_conditions"]),
        )

    def clear_all(conn: sqlite3.Connection) -> None:
        conn.execute("DELETE FROM patients")
        conn.commit()
