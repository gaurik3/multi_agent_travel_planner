from state import TravelPlanState
from utils.failure_classifier import classify_failure, get_exit_reason
from utils.logger import persist_run_record


def safe_exit_node(state: TravelPlanState) -> TravelPlanState:
    failure_type = classify_failure(state)
    exit_reason  = get_exit_reason(failure_type, state)

    persist_run_record(
        run_id=state.get("run_id", "unknown"),
        destination=state.get("destination", "unknown"),
        status="failed",
        failure_type=failure_type,
        exit_reason=exit_reason,
        total_tokens=state.get("total_tokens_in", 0) + state.get("total_tokens_out", 0),
        total_cost_usd=state.get("total_cost_usd", 0.0),
        duration_seconds=0.0
    )

    final = f"""
=== TRAVEL PLANNING INCOMPLETE ===

Run ID      : {state.get("run_id", "unknown")}
Failure type: {failure_type}
Reason      : {exit_reason}

Completed steps:
  Research   : {"✓" if state.get("destination_info") else "✗"}
  Budget     : {"✓" if state.get("budget_breakdown") else "✗"}
  Flights    : {"✓" if state.get("flight_options") else "✗"}
  Hotels     : {"✓" if state.get("hotel_options") else "✗"}
  Itinerary  : {"✓" if state.get("itinerary") else "✗"}
  Validation : {"✓" if state.get("validation_notes") else "✗"}

Please try again or review logs for run ID: {state.get("run_id")}
    """.strip()

    print(final)

    return {
        **state,
        "final_plan":   final,
        "failure_type": failure_type,
        "status":       "failed",
    }
