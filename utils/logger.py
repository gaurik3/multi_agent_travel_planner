import sqlite3
import json
import os
import time
from datetime import datetime
from typing import Optional

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "runs.db")


def _get_connection() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    return sqlite3.connect(DB_PATH)


def init_db():
    """Create tables if they don't exist. Call once at startup in main.py."""
    conn = _get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS llm_calls (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id          TEXT NOT NULL,
            agent_name      TEXT NOT NULL,
            prompt_version  TEXT NOT NULL,
            deployment_name TEXT NOT NULL,
            tokens_in       INTEGER,
            tokens_out      INTEGER,
            latency_ms      REAL,
            retry_count     INTEGER DEFAULT 0,
            success         INTEGER NOT NULL,
            error_message   TEXT,
            cost_usd        REAL,
            timestamp       TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS run_records (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id           TEXT NOT NULL UNIQUE,
            destination      TEXT,
            status           TEXT NOT NULL,
            failure_type     TEXT,
            exit_reason      TEXT,
            total_tokens     INTEGER,
            total_cost_usd   REAL,
            duration_seconds REAL,
            timestamp        TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def log_llm_call(
    run_id: str,
    agent_name: str,
    prompt_version: str,
    deployment_name: str,
    tokens_in: int,
    tokens_out: int,
    latency_ms: float,
    retry_count: int,
    success: bool,
    cost_usd: float,
    error_message: Optional[str] = None
):
    """
    Persist one LLM call record to SQLite.
    Call this inside call_llm_safe() after every LLM invocation attempt.
    """
    conn = _get_connection()
    conn.execute("""
        INSERT INTO llm_calls (
            run_id, agent_name, prompt_version, deployment_name,
            tokens_in, tokens_out, latency_ms, retry_count,
            success, error_message, cost_usd, timestamp
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        run_id,
        agent_name,
        prompt_version,
        deployment_name,
        tokens_in,
        tokens_out,
        latency_ms,
        retry_count,
        1 if success else 0,
        error_message,
        cost_usd,
        datetime.utcnow().isoformat()
    ))
    conn.commit()
    conn.close()


def get_run_logs(run_id: str) -> list:
    """Retrieve all LLM call logs for a given run_id."""
    conn = _get_connection()
    cursor = conn.execute(
        "SELECT * FROM llm_calls WHERE run_id = ? ORDER BY id ASC",
        (run_id,)
    )
    columns = [desc[0] for desc in cursor.description]
    rows = [dict(zip(columns, row)) for row in cursor.fetchall()]
    conn.close()
    return rows


def export_run_logs_jsonl(run_id: str, output_path: str):
    """Export all logs for a run to a JSONL file."""
    logs = get_run_logs(run_id)
    with open(output_path, "w") as f:
        for log in logs:
            f.write(json.dumps(log) + "\n")


def persist_run_record(
    run_id: str,
    destination: str,
    status: str,
    failure_type: Optional[str],
    exit_reason: Optional[str],
    total_tokens: int,
    total_cost_usd: float,
    duration_seconds: float
):
    """Persist a summary record for the full run. Call at END and at safe_exit."""
    conn = _get_connection()
    conn.execute("""
        INSERT OR REPLACE INTO run_records (
            run_id, destination, status, failure_type, exit_reason,
            total_tokens, total_cost_usd, duration_seconds, timestamp
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        run_id,
        destination,
        status,
        failure_type,
        exit_reason,
        total_tokens,
        total_cost_usd,
        round(duration_seconds, 2),
        datetime.utcnow().isoformat()
    ))
    conn.commit()
    conn.close()
