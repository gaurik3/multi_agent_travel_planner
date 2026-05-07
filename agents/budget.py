import json
from state import TravelPlanState
from utils.llm import call_llm_safe
from utils.error_handler import safe_node
from utils.prompt_loader import load_prompt


@safe_node
def budget_node(state: TravelPlanState) -> TravelPlanState:
    destination   = state["destination"]
    origin        = state["origin"]
    budget_inr    = state["budget_inr"]
    num_travelers = state["num_travelers"]
    travel_dates  = state["travel_dates"]

    print(f"\n[BUDGET AGENT] Calling LLM to plan budget of Rs {budget_inr:,.0f}...")

    prompt_config  = load_prompt("budget")
    system_message = prompt_config["system_message"]
    temperature    = prompt_config["temperature"]
    max_tokens     = prompt_config["max_tokens"]
    prompt_version = prompt_config["prompt_version"]

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

    result = call_llm_safe(
        prompt=user_prompt,
        system=system_message,
        agent_name="budget",
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
            "budget": prompt_version,
        },
    }

    if not result["success"]:
        return {**state, "error_message": result["error"], "status": "failed"}

    raw   = result["content"]
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
