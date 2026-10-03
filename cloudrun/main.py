import os
import json
import sqlite3
import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False

# Configure structured logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("contact-validator-service")

app = FastAPI(
    title="WF-006 Contact Ingestion & Validation Service",
    version="1.0.0",
    description="Validates and persists incoming contacts for the WF-006 Google Cloud Architecture"
)

# Configuration from Environment Variables
USE_POSTGRES = os.getenv("USE_POSTGRES", "false").lower() in ("1", "true", "yes")
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_NAME = os.getenv("DB_NAME", "wf006_db")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_SSLMODE = os.getenv("DB_SSLMODE", "prefer")
LOCAL_SQLITE_PATH = os.getenv("LOCAL_SQLITE_PATH", "wf006_local.db")


def init_local_sqlite():
    """Initializes local SQLite schema if running locally without Cloud SQL."""
    try:
        with sqlite3.connect(LOCAL_SQLITE_PATH) as sconn:
            cur = sconn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS contacts (
                    contact_id TEXT PRIMARY KEY,
                    name TEXT,
                    phone TEXT,
                    email TEXT,
                    source TEXT NOT NULL,
                    owner TEXT NOT NULL,
                    consent_status TEXT DEFAULT 'PENDING',
                    dnd_status BOOLEAN DEFAULT 0,
                    created_at TEXT,
                    updated_at TEXT
                );
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS contact_audit_log (
                    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    contact_id TEXT NOT NULL,
                    decision TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    metadata TEXT,
                    created_at TEXT
                );
            """)
            sconn.commit()
    except Exception as e:
        logger.warning(f"Could not initialize local SQLite db: {e}")

# Initialize SQLite tables on startup
init_local_sqlite()


class ContactRecord(BaseModel):
    Contact_ID: str = Field(..., min_length=1, max_length=64, description="Mandatory master contact identifier")
    name: Optional[str] = Field(None, max_length=255, description="Full name of contact")
    phone: Optional[str] = Field(None, max_length=32, description="E.164 phone / WhatsApp number")
    email: Optional[str] = Field(None, max_length=255, description="Email address")
    source: str = Field(..., min_length=1, max_length=64, description="Origin source system (CRM, CSV, WhatsApp, ERP)")
    owner: str = Field(..., min_length=1, max_length=128, description="Assigned owner or department")
    consent_status: Optional[str] = Field("PENDING", max_length=32, description="GRANTED, REVOKED, or PENDING")
    dnd_status: Optional[bool] = Field(False, description="Initial DND flag before verification")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ValidationResponse(BaseModel):
    status: str
    is_valid: bool
    contact: ContactRecord
    validation_timestamp: datetime
    message: str


class AuditLogRequest(BaseModel):
    contact_id: str
    decision: str  # APPROVED, BLOCKED, REJECTED
    reason: str
    details: Optional[dict] = None


def get_db_connection():
    """Establish connection to Cloud SQL PostgreSQL if enabled and available."""
    if not USE_POSTGRES or not PSYCOPG2_AVAILABLE:
        return None
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            sslmode=DB_SSLMODE,
            connect_timeout=2
        )
        return conn
    except Exception as exc:
        logger.warning(f"Cloud SQL connection failed ({exc}). Falling back to local SQLite.")
        return None


@app.get("/health")
def health_check():
    return {
        "service": "wf006-cloudrun",
        "status": "healthy",
        "database_backend": "PostgreSQL" if USE_POSTGRES and PSYCOPG2_AVAILABLE else f"Local SQLite ({LOCAL_SQLITE_PATH})",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }



@app.post("/validate", response_model=ValidationResponse, status_code=status.HTTP_200_OK)
def validate_contact(payload: ContactRecord):
    """
    Business Rules Validation:
    - Every contact must have Contact_ID
    - Every contact must have a source
    - Every contact must have an owner
    - Must provide at least one reachable address (phone or email)
    """
    logger.info(f"Validating contact: Contact_ID={payload.Contact_ID}, source={payload.source}, owner={payload.owner}")

    # Validate reachable identity
    if not payload.phone and not payload.email:
        logger.error(f"Validation failed for {payload.Contact_ID}: Missing both phone and email")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Contact must include at least a phone number or an email address."
        )

    # Set timestamps if absent
    now = datetime.now(timezone.utc)
    if not payload.created_at:
        payload.created_at = now
    payload.updated_at = now

    return ValidationResponse(
        status="SUCCESS",
        is_valid=True,
        contact=payload,
        validation_timestamp=now,
        message="Contact passed all schema and mandatory attribute validations."
    )


@app.post("/persist", status_code=status.HTTP_200_OK)
def persist_master_contact(payload: ContactRecord):
    """
    Stores approved contact in Cloud SQL PostgreSQL or local SQLite master table.
    Also logs the audit entry.
    """
    logger.info(f"Persisting approved contact {payload.Contact_ID}")
    conn = get_db_connection()

    if not conn:
        # Save to local SQLite
        try:
            with sqlite3.connect(LOCAL_SQLITE_PATH) as sconn:
                cur = sconn.cursor()
                cur.execute("""
                    INSERT INTO contacts (
                        contact_id, name, phone, email, source, owner,
                        consent_status, dnd_status, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(contact_id) DO UPDATE SET
                        name = excluded.name,
                        phone = excluded.phone,
                        email = excluded.email,
                        source = excluded.source,
                        owner = excluded.owner,
                        consent_status = excluded.consent_status,
                        dnd_status = excluded.dnd_status,
                        updated_at = excluded.updated_at;
                """, (
                    payload.Contact_ID, payload.name, payload.phone, payload.email,
                    payload.source, payload.owner, payload.consent_status,
                    1 if payload.dnd_status else 0,
                    str(payload.created_at), str(payload.updated_at)
                ))
                cur.execute("""
                    INSERT INTO contact_audit_log (contact_id, decision, reason, metadata, created_at)
                    VALUES (?, ?, ?, ?, ?);
                """, (
                    payload.Contact_ID,
                    "APPROVED",
                    "Passed validation and DND verification. Saved as master record.",
                    json.dumps(payload.model_dump(), default=str),
                    datetime.now(timezone.utc).isoformat()
                ))
                sconn.commit()

            return {
                "status": "PERSISTED",
                "contact_id": payload.Contact_ID,
                "storage": f"Local SQLite ({LOCAL_SQLITE_PATH})",
                "message": "Master record and audit log saved successfully."
            }
        except Exception as exc:
            logger.error(f"Error persisting to local SQLite: {exc}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))

    try:
        with conn.cursor() as cur:
            # 1. Upsert into contacts table
            upsert_query = """
                INSERT INTO contacts (
                    contact_id, name, phone, email, source, owner,
                    consent_status, dnd_status, created_at, updated_at
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
                ON CONFLICT (contact_id) DO UPDATE SET
                    name = EXCLUDED.name,
                    phone = EXCLUDED.phone,
                    email = EXCLUDED.email,
                    source = EXCLUDED.source,
                    owner = EXCLUDED.owner,
                    consent_status = EXCLUDED.consent_status,
                    dnd_status = EXCLUDED.dnd_status,
                    updated_at = EXCLUDED.updated_at;
            """
            cur.execute(
                upsert_query,
                (
                    payload.Contact_ID,
                    payload.name,
                    payload.phone,
                    payload.email,
                    payload.source,
                    payload.owner,
                    payload.consent_status,
                    payload.dnd_status,
                    payload.created_at,
                    payload.updated_at
                )
            )

            # 2. Insert audit log
            audit_query = """
                INSERT INTO contact_audit_log (
                    contact_id, decision, reason, metadata, created_at
                ) VALUES (%s, %s, %s, %s, %s);
            """
            cur.execute(
                audit_query,
                (
                    payload.Contact_ID,
                    "APPROVED",
                    "Passed validation and DND verification. Saved as master record.",
                    json.dumps(payload.model_dump(), default=str),
                    datetime.now(timezone.utc)
                )
            )

            conn.commit()

        return {
            "status": "PERSISTED",
            "contact_id": payload.Contact_ID,
            "storage": "Cloud SQL PostgreSQL",
            "message": "Master record and audit log saved to Cloud SQL."
        }
    except Exception as exc:
        conn.rollback()
        logger.error(f"Error persisting contact {payload.Contact_ID}: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database write error: {str(exc)}"
        )
    finally:
        conn.close()


@app.post("/audit-log", status_code=status.HTTP_200_OK)
def record_audit_log(audit: AuditLogRequest):
    """
    Records an audit log entry (e.g. for DND blocked contacts).
    """
    logger.info(f"Logging decision for {audit.contact_id}: decision={audit.decision}, reason={audit.reason}")
    conn = get_db_connection()

    if not conn:
        try:
            with sqlite3.connect(LOCAL_SQLITE_PATH) as sconn:
                cur = sconn.cursor()
                cur.execute("""
                    INSERT INTO contact_audit_log (contact_id, decision, reason, metadata, created_at)
                    VALUES (?, ?, ?, ?, ?);
                """, (
                    audit.contact_id,
                    audit.decision,
                    audit.reason,
                    json.dumps(audit.details or {}),
                    datetime.now(timezone.utc).isoformat()
                ))
                sconn.commit()
            return {
                "status": "AUDIT_LOGGED",
                "contact_id": audit.contact_id,
                "storage": f"Local SQLite ({LOCAL_SQLITE_PATH})",
                "decision": audit.decision
            }
        except Exception as exc:
            logger.error(f"Error writing audit log to local SQLite: {exc}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))

    try:
        with conn.cursor() as cur:
            audit_query = """
                INSERT INTO contact_audit_log (
                    contact_id, decision, reason, metadata, created_at
                ) VALUES (%s, %s, %s, %s, %s);
            """
            cur.execute(
                audit_query,
                (
                    audit.contact_id,
                    audit.decision,
                    audit.reason,
                    json.dumps(audit.details or {}),
                    datetime.now(timezone.utc)
                )
            )
            conn.commit()

        return {"status": "AUDIT_LOGGED", "contact_id": audit.contact_id, "storage": "Cloud SQL"}
    except Exception as exc:
        conn.rollback()
        logger.error(f"Error writing audit log for {audit.contact_id}: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Audit write error: {str(exc)}"
        )
    finally:
        conn.close()


@app.get("/contacts")
def get_contacts():
    """Lists all persisted contacts (from Cloud SQL or local SQLite)."""
    conn = get_db_connection()
    if not conn:
        with sqlite3.connect(LOCAL_SQLITE_PATH) as sconn:
            sconn.row_factory = sqlite3.Row
            rows = sconn.execute("SELECT * FROM contacts ORDER BY created_at DESC").fetchall()
            return [dict(r) for r in rows]

    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM contacts ORDER BY created_at DESC")
            return cur.fetchall()
    finally:
        conn.close()


@app.get("/audit-logs")
def get_audit_logs():
    """Lists all audit log decisions (from Cloud SQL or local SQLite)."""
    conn = get_db_connection()
    if not conn:
        with sqlite3.connect(LOCAL_SQLITE_PATH) as sconn:
            sconn.row_factory = sqlite3.Row
            rows = sconn.execute("SELECT * FROM contact_audit_log ORDER BY created_at DESC").fetchall()
            return [dict(r) for r in rows]

    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM contact_audit_log ORDER BY created_at DESC")
            return cur.fetchall()
    finally:
        conn.close()

