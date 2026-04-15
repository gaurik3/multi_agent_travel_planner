import json
from state import TravelPlanState
from utils.llm import call_llm_safe
from utils.error_handler import safe_node

SYSTEM = """You are a hotel search expert who generates realistic accommodation options.
You create plausible hotel data using real hotel names, realistic prices, and accurate
location descriptions. Always respond with valid JSON only — no markdown fences, no extra text."""

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

    raw   = call_llm_safe(SYSTEM, user_prompt)
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