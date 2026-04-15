from state import TravelPlanState

ROUTE_MAP = {
    "start":           "research",
    "research":        "budget",
    "budget":          "flights",
    "flights":         "checkpoint_1",
    "checkpoint_1":    "hotels",
    "hotels":          "itinerary",
    "itinerary":       "validate",
    "validate":        "checkpoint_2",
    "checkpoint_2":    "final_plan",
    "final_plan":      "end",
    "retry_flights":   "flights",
    "retry_itinerary": "itinerary",
}

VALID_TARGETS = {
    "research", "budget", "flights", "checkpoint_1",
    "hotels", "itinerary", "validate", "checkpoint_2",
    "final_plan", "failed", "end",
}


def orchestrator_node(state: TravelPlanState) -> TravelPlanState:
    current = state.get("status") or "start"
    retry   = state.get("retry_count", 0)

    print(f"\n[ORCHESTRATOR] status='{current}'  retry_count={retry}")

    if retry >= 3:
        msg = f"Maximum retries reached (retry_count={retry}). Last status: '{current}'."
        print(f"[ORCHESTRATOR] ⚠  {msg}")
        return {
            **state,
            "error_message": msg,
            "status": "failed",
        }

    if current == "failed":
        print("[ORCHESTRATOR] Agent reported failure — routing to safe exit")
        return {**state, "status": "failed"}

    next_status = ROUTE_MAP.get(current, "failed")

    if next_status == "failed":
        msg = f"Unknown status '{current}' — no route defined."
        print(f"[ORCHESTRATOR] ⚠  {msg}")
        return {**state, "error_message": msg, "status": "failed"}

    print(f"[ORCHESTRATOR] '{current}' -> '{next_status}'")
    return {**state, "status": next_status}


def route_by_status(state: TravelPlanState) -> str:
    status = state.get("status", "failed")
    retry  = state.get("retry_count", 0)

    if retry >= 3:
        return "failed"

    if status in VALID_TARGETS:
        return status

    return "failed"