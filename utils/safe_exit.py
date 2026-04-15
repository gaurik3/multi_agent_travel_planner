from state import TravelPlanState

def safe_exit_node(state: TravelPlanState) -> TravelPlanState:
    error  = state.get("error_message") or "Unknown error — no error_message was set."
    retry  = state.get("retry_count", 0)
    status = state.get("status", "unknown")

    W     = 60
    thick = "═" * W
    thin  = "─" * W

    lines = [
        "",
        thick,
        "  ❌  TRAVEL PLANNER — SAFE EXIT",
        thick,
        f"  Last status : {status}",
        f"  Retry count : {retry}",
        f"  Error       : {error}",
        thin,
        "  What you can do:",
        "    1. Check your .env file and Azure credentials",
        "    2. Retry — transient API errors often resolve on re-run",
        "    3. Simplify your inputs (shorter dates, closer destination)",
        "    4. Check the full traceback printed above for details",
        thick,
    ]

    message = "\n".join(lines)
    print(message)

    return {
        **state,
        "final_plan": message,
        "status":     "failed",
    }