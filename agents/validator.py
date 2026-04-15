from state import TravelPlanState
from utils.llm import call_llm_safe
from utils.error_handler import safe_node

SYSTEM = """You are a meticulous travel plan reviewer. You check itineraries for
logical errors, budget consistency, scheduling conflicts, and practical issues.
Be concise and specific. If everything looks good, say so clearly."""

@safe_node
def validator_node(state: TravelPlanState) -> TravelPlanState:
    print(f"\n[VALIDATOR AGENT] Running validation checks...")

    sf            = state.get("selected_flight", {})
    hotel_options = state.get("hotel_options", [])
    budget_inr    = state.get("budget_inr", 0)
    budget        = state.get("budget_breakdown", {})

    local_issues = []

    if not sf:
        local_issues.append("No flight selected.")
    if not hotel_options:
        local_issues.append("No hotel options generated.")
    if not state.get("itinerary"):
        local_issues.append("Itinerary is empty.")

    flight_cost = sf.get("total_price_inr", 0)
    hotel_cost  = hotel_options[0].get("total_price_inr", 0) if hotel_options else 0
    est_total   = flight_cost + hotel_cost + budget.get("food_total", 0) + budget.get("activities_total", 0)

    if est_total > budget_inr * 1.05:
        local_issues.append(
            f"Estimated total Rs {est_total:,} exceeds budget "
            f"Rs {budget_inr:,.0f} by more than 5%."
        )

    if local_issues:
        notes = "LOCAL CHECKS FAILED:\n" + "\n".join(f"  - {i}" for i in local_issues)
        print(f"  [WARN] {len(local_issues)} local issue(s): {local_issues}")
        return {**state, "validation_notes": notes, "status": "validate"}

    print(f"  [OK] Local checks passed — calling LLM for deep review...")

    user_prompt = f"""Review this travel plan for issues.

TRIP:
- Destination : {state.get('destination')}
- Dates       : {state.get('travel_dates')}
- Travellers  : {state.get('num_travelers')}
- Budget      : Rs {budget_inr:,.0f}

FLIGHT: {sf.get('airline')} | {sf.get('route')}
Departs: {sf.get('departure')} | Arrives: {sf.get('arrival')}
Cost: Rs {sf.get('total_price_inr',0):,}

HOTEL (Option 1): {hotel_options[0].get('name')}
Check-in: {hotel_options[0].get('check_in')} | Check-out: {hotel_options[0].get('check_out')}
Cost: Rs {hotel_options[0].get('total_price_inr',0):,}

ITINERARY EXCERPT:
{state.get('itinerary','')[:600]}...

CHECK FOR:
1. Hotel dates match flight arrival/departure?
2. Day 1 appropriate for arrival (not overpacked)?
3. Last day allows enough time to reach airport?
4. Any scheduling conflicts?
5. Overall plan realistic for the budget?

Respond with either:
"All checks passed." + 2-3 sentence summary
OR
"Issues found:" + numbered list of problems

No markdown."""

    try:
        notes = call_llm_safe(SYSTEM, user_prompt).strip()
        print(f"  [OK] LLM review complete")
    except Exception as e:
        print(f"  [WARN] LLM validation unavailable ({e}) — using local result")
        notes = "All checks passed (LLM review unavailable — local checks passed)."

    return {
        **state,
        "validation_notes": notes,
        "status":           "validate",
    }