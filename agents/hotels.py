import json
from state import TravelPlanState
from utils.llm import call_llm_safe
from utils.error_handler import safe_node
from utils.prompt_loader import load_prompt


@safe_node
def hotels_node(state: TravelPlanState) -> TravelPlanState:
    destination     = state["destination"]
    budget          = state["budget_breakdown"]
    selected_flight = state.get("selected_flight", {})
    num_travelers   = state["num_travelers"]
    travel_dates    = state["travel_dates"]

    checkin      = selected_flight.get("arrival", "as per travel dates")
    hotel_budget = budget.get("hotels_total", 0)

    print(f"\n[HOTELS AGENT] Calling LLM for hotels in '{destination}'...")

    prompt_config  = load_prompt("hotels")
    system_message = prompt_config["system_message"]
    temperature    = prompt_config["temperature"]
    max_tokens     = prompt_config["max_tokens"]
    prompt_version = prompt_config["prompt_version"]

    user_prompt = f"""Generate 3 realistic hotel options for this stay.

Trip details:
- Destination  : {destination}
- Travellers   : {num_travelers}
- Travel dates : {travel_dates}
- Hotel budget : Rs {hotel_budget:,} total for entire stay
- Flight arrives: {checkin}

Return a JSON array of exactly 3 hotel objects with these exact keys:
{{
  "option": <1, 2, or 3>,
  "name": "Hotel name",
  "stars": <1-5>,
  "location": "Neighbourhood and proximity to attractions/transport",
  "check_in":  "DD Mon YYYY",
  "check_out": "DD Mon YYYY",
  "price_per_night_inr": <integer>,
  "total_price_inr": <integer>,
  "pros": "2-3 pros",
  "cons": "1-2 cons"
}}

Option 1: best fit at or under Rs {hotel_budget:,}.
Option 2: mid-range upgrade, 20-40% over budget.
Option 3: budget option, 20-30% under budget.
Dates must match: {travel_dates}.
Return only the JSON array."""

    result = call_llm_safe(
        prompt=user_prompt,
        system=system_message,
        agent_name="hotels",
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
            "hotels": prompt_version,
        },
    }

    if not result["success"]:
        return {**state, "error_message": result["error"], "status": "failed"}

    raw   = result["content"]
    clean = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    data  = json.loads(clean)

    if not isinstance(data, list) or len(data) != 3:
        raise ValueError(f"Expected list of 3 hotels, got {type(data).__name__} len={len(data) if isinstance(data, list) else 'N/A'}")

    print(f"  [OK] Got {len(data)} hotel options")
    for opt in data:
        print(f"       Option {opt['option']}: {opt['name']} ({opt['stars']}★) — Rs {opt['total_price_inr']:,}")

    return {
        **state,
        "hotel_options": data,
        "status":        "hotels",
    }
