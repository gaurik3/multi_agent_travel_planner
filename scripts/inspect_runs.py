"""
Usage: python scripts/inspect_run.py <run_id>
Prints all LLM call logs and the run record for a given run_id.
"""
import sys
import json
import sqlite3
import os

# Allow imports from project root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from utils.logger import get_run_logs

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "runs.db")


def inspect_run(run_id: str):
    print(f"\n=== LLM Calls for run: {run_id} ===")
    logs = get_run_logs(run_id)
    if not logs:
        print("No logs found for this run_id.")
    for log in logs:
        print(json.dumps(log, indent=2))

    print(f"\n=== Run Record ===")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.execute(
        "SELECT * FROM run_records WHERE run_id = ?", (run_id,)
    )
    columns = [d[0] for d in cursor.description]
    row = cursor.fetchone()
    if row:
        print(json.dumps(dict(zip(columns, row)), indent=2))
    else:
        print("No run record found.")
    conn.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/inspect_run.py <run_id>")
        sys.exit(1)
    inspect_run(sys.argv[1])
