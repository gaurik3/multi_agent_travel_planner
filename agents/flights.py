import json
from state import TravelPlanState
from utils.llm import call_llm_safe
from utils.error_handler import safe_node

SYSTEM = """You are a flight search expert who generates realistic flight options.
You create plausible flight data using real airlines, real routes, and realistic
prices and timings. Always respond with valid JSON only — no markdown fences, no extra text."""

@safe_node
def flights_node(state: TravelPlanState) -> TravelPlanState:
    origin        = state["origin"]
    destination   = state["destination"]
    travel_dates  = state["travel_dates"]
    budget        = state["budget_breakdown"]
    num_travelers = state["num_travelers"]
    retry_count   = state.get("retry_count", 0)

    flight_budget = budget.get("flights_per_person", 0) * num_travelers

    print(f"\n[FLIGHTS AGENT] Calling LLM for flights {origin} -> {destination}...")

    retry_note = ""
    if retry_count > 0:
        retry_note = (
            f"\nNote: The user rejected the previous options (attempt {retry_count}). "
            "Please suggest different airlines or routings than before."
        )

    user_prompt = f"""Generate 3 realistic flight options for this route.
{retry_note}
Trip details:
- Origin        : {origin}
- Destination   : {destination}
- Travel dates  : {travel_dates}
- Travellers    : {num_travelers}
- Flight budget : Rs {flight_budget:,} total (Rs {budget.get('flights_per_person',0):,}/person)

Return a JSON array of exactly 3 flight objects with these exact keys:
{{
  "option": <1, 2, or 3>,
  "airline": "Airline name and flight numbers",
  "route": "IATA_ORIGIN -> IATA_DEST (stop info)",
  "departure": "DD Mon YYYY, HH:MM (CITY)",
  "arrival": "DD Mon YYYY, HH:MM (CITY)",
  "duration": "Xh Ym (non-stop or N stop)",
  "price_per_person_inr": <integer>,
  "total_price_inr": <integer>,
  "pros": "2-3 pros",
  "cons": "1-2 cons"
}}

Option 1: best value near or under budget.
Option 2: premium — better experience, slightly over budget.
Option 3: a different routing or airline.
Return only the JSON array."""

    raw   = call_llm_safe(SYSTEM, user_prompt)
    clean = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    data  = json.loads(clean)

    if not isinstance(data, list) or len(data) != 3:
        raise ValueError(f"Expected list of 3 flights, got {type(data).__name__} len={len(data) if isinstance(data, list) else 'N/A'}")

    print(f"  [OK] Got {len(data)} flight options")
    for opt in data:
        print(f"       Option {opt['option']}: {opt['airline']} — Rs {opt['total_price_inr']:,}")

    return {
        **state,
        "flight_options": data,
        "status":         "flights",
    }