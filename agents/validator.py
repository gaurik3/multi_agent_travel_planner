from state import TravelPlanState
from utils.llm import call_llm_safe
from utils.error_handler import safe_node
from utils.prompt_loader import load_prompt


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

    prompt_config  = load_prompt("validator")
    system_message = prompt_config["system_message"]
    temperature    = prompt_config["temperature"]
    max_tokens     = prompt_config["max_tokens"]
    prompt_version = prompt_config["prompt_version"]

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

    result = call_llm_safe(
        prompt=user_prompt,
        system=system_message,
        agent_name="validator",
        prompt_version=prompt_version,
        run_id=state.get("run_id", "unknown"),
        temperature=temperature,
        max_tokens=max_tokens,
    )

    state = {
        **state,
        "total_tokens_in":  state.get("total_tokens_in",  0) + result["tokens_in"],
        "total_tokens_out": state.get("total_tokens_out", 0) + result["tokens_out"],
        "total_cost_usd":   state.get("total_cost_usd",   0.0) + result["cost_usd"],
        "prompt_versions_used": {
            **state.get("prompt_versions_used", {}),
            "validator": prompt_version,
        },
    }

    if not result["success"]:
        notes = "All checks passed (LLM review unavailable — local checks passed)."
        print(f"  [WARN] LLM validation unavailable ({result['error']}) — using local result")
    else:
        notes = result["content"].strip()
        print(f"  [OK] LLM review complete")

    return {
        **state,
        "validation_notes": notes,
        "status":           "validate",
    }
