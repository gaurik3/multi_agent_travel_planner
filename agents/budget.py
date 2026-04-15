import json
from state import TravelPlanState
from utils.llm import call_llm_safe
from utils.error_handler import safe_node

SYSTEM = """You are an expert travel budget planner specialising in trips from India.
You know current flight prices, hotel rates, and daily living costs worldwide.
Always respond with valid JSON only — no markdown fences, no extra text."""

@safe_node
def budget_node(state: TravelPlanState) -> TravelPlanState:
    destination   = state["destination"]
    origin        = state["origin"]
    budget_inr    = state["budget_inr"]
    num_travelers = state["num_travelers"]
    travel_dates  = state["travel_dates"]

    print(f"\n[BUDGET AGENT] Calling LLM to plan budget of Rs {budget_inr:,.0f}...")

    user_prompt = f"""Create a realistic travel budget breakdown for this trip.

Trip details:
- Origin      : {origin}
- Destination : {destination}
- Dates       : {travel_dates}
- Travellers  : {num_travelers}
- Total budget: Rs {budget_inr:,.0f} INR

Return exactly this JSON structure with integer INR values:
{{
  "flights_per_person": <integer INR>,
  "hotels_total":       <integer INR>,
  "food_total":         <integer INR>,
  "activities_total":   <integer INR>,
  "buffer":             <integer INR>,
  "total":              <integer INR — must equal flights_per_person*{num_travelers} + hotels_total + food_total + activities_total + buffer>,
  "notes":              "2-3 sentences of budget strategy advice"
}}

The total must be at or under Rs {budget_inr:,.0f}.
Return only the JSON object."""

    raw   = call_llm_safe(SYSTEM, user_prompt)
    clean = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    data  = json.loads(clean)

    required = ["flights_per_person", "hotels_total", "food_total",
                "activities_total", "buffer", "total", "notes"]
    missing = [k for k in required if k not in data]
    if missing:
        raise ValueError(f"Budget response missing keys: {missing}")

    print(f"  [OK] Budget planned — total Rs {data['total']:,}")

    return {
        **state,
        "budget_breakdown": data,
        "status":           "budget",
    }