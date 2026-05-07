from typing import TypedDict, Any


class TravelPlanState(TypedDict):
    # ── User inputs ───────────────────────────────────────────────
    destination: str
    origin: str
    travel_dates: str
    num_travelers: int
    budget_inr: float

    # ── Agent outputs ─────────────────────────────────────────────
    destination_info: str
    visa_info: str
    best_travel_tips: str
    budget_breakdown: dict
    flight_options: list
    selected_flight: dict
    hotel_options: list
    selected_hotel: dict
    itinerary: str
    validation_notes: str

    # ── Human interaction ─────────────────────────────────────────
    human_feedback_1: str
    human_feedback_2: str

    # ── Control flow ──────────────────────────────────────────────
    status: str
    retry_count: int
    error_message: str
    failure_type: str       # set by safe_exit_node via Module 4

    # ── Final output ──────────────────────────────────────────────
    final_plan: str

    # ── Module 1: Prompt versioning ───────────────────────────────
    prompt_versions_used: dict  # e.g. {"research": "research-v1", ...}

    # ── Module 2 + 3: Observability and cost tracking ─────────────
    run_id: str
    total_tokens_in: int
    total_tokens_out: int
    total_cost_usd: float

    # ── Module 6: Classifier ──────────────────────────────────────
    travel_style: str  # set before graph starts: budget/mid-range/luxury/adventure
