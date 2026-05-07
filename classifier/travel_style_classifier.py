import yaml
import os
import sqlite3
from datetime import datetime

METADATA_PATH = os.path.join(os.path.dirname(__file__), "model_metadata.yaml")
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "runs.db")


def _load_metadata() -> dict:
    with open(METADATA_PATH, "r") as f:
        return yaml.safe_load(f)


def _infer_destination_type(destination: str) -> str:
    """Simple keyword-based destination type inference."""
    destination = destination.lower()
    adventure_keywords = ["trek", "safari", "bali", "nepal", "rishikesh", "ladakh"]
    beach_keywords     = ["goa", "maldives", "phuket", "bali", "hawaii", "cancun"]
    mountain_keywords  = ["shimla", "manali", "darjeeling", "alps", "swiss", "colorado"]

    for kw in adventure_keywords:
        if kw in destination:
            return "adventure"
    for kw in beach_keywords:
        if kw in destination:
            return "beach"
    for kw in mountain_keywords:
        if kw in destination:
            return "mountain"
    return "city"


def classify_travel_style(
    budget_inr: float,
    num_travelers: int,
    travel_dates: str,
    destination: str,
    run_id: str
) -> dict:
    """
    Classifies travel style and logs the inference result.

    Returns:
    {
        "travel_style": str,
        "budget_per_person_per_day": float,
        "destination_type": str,
        "model_version": str,
        "training_data_version": str
    }
    """
    metadata = _load_metadata()

    # Estimate number of days from travel_dates string
    # Expects format like "15 June 2025 to 25 June 2025"
    try:
        from datetime import datetime as dt
        parts = travel_dates.split(" to ")
        start = dt.strptime(parts[0].strip(), "%d %B %Y")
        end   = dt.strptime(parts[1].strip(), "%d %B %Y")
        num_days = max((end - start).days, 1)
    except Exception:
        num_days = 7  # default fallback

    budget_ppd = budget_inr / max(num_travelers, 1) / num_days
    dest_type  = _infer_destination_type(destination)
    thresholds = metadata["thresholds"]

    # Classification logic
    if dest_type == "adventure" and budget_ppd >= 3000:
        travel_style = "adventure"
    elif budget_ppd < thresholds["budget_upper"]:
        travel_style = "budget"
    elif budget_ppd < thresholds["mid_range_upper"]:
        travel_style = "mid-range"
    else:
        travel_style = "luxury"

    result = {
        "travel_style":              travel_style,
        "budget_per_person_per_day": round(budget_ppd, 2),
        "destination_type":          dest_type,
        "model_version":             metadata["model_version"],
        "training_data_version":     metadata["training_data_version"]
    }

    # Log inference to SQLite
    _log_inference(run_id, result)

    return result


def _log_inference(run_id: str, result: dict):
    """Persist the classifier inference result to SQLite."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS classifier_inferences (
            id                        INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id                    TEXT NOT NULL,
            travel_style              TEXT NOT NULL,
            budget_per_person_per_day REAL,
            destination_type          TEXT,
            model_version             TEXT,
            training_data_version     TEXT,
            timestamp                 TEXT NOT NULL
        )
    """)
    conn.execute("""
        INSERT INTO classifier_inferences (
            run_id, travel_style, budget_per_person_per_day,
            destination_type, model_version, training_data_version, timestamp
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        run_id,
        result["travel_style"],
        result["budget_per_person_per_day"],
        result["destination_type"],
        result["model_version"],
        result["training_data_version"],
        datetime.utcnow().isoformat()
    ))
    conn.commit()
    conn.close()
