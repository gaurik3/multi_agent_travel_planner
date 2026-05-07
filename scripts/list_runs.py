"""
Usage: python scripts/list_runs.py
Lists all past runs with their status, destination, and cost.
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "runs.db")


def list_runs():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.execute(
        "SELECT run_id, destination, status, failure_type, total_cost_usd, timestamp "
        "FROM run_records ORDER BY timestamp DESC"
    )
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        print("No runs found.")
        return

    print(f"\n{'RUN ID':<12} {'DESTINATION':<20} {'STATUS':<12} "
          f"{'FAILURE':<22} {'COST USD':<10} TIMESTAMP")
    print("-" * 90)
    for row in rows:
        run_id, dest, status, failure, cost, ts = row
        print(f"{run_id:<12} {(dest or ''):<20} {status:<12} "
              f"{(failure or '-'):<22} {(cost or 0):<10.4f} {ts}")


if __name__ == "__main__":
    list_runs()
