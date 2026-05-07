from state import TravelPlanState
from utils.llm import call_llm_safe
from utils.error_handler import safe_node
from utils.prompt_loader import load_prompt


@safe_node
def itinerary_node(state: TravelPlanState) -> TravelPlanState:
    destination     = state["destination"]
    travel_dates    = state["travel_dates"]
    dest_info       = state.get("destination_info", "")
    tips            = state.get("best_travel_tips", "")
    selected_flight = state.get("selected_flight", {})
    selected_hotel  = state.get("selected_hotel", {})
    budget          = state.get("budget_breakdown", {})
    feedback        = state.get("human_feedback_2", "")
    travel_style    = state.get("travel_style", "mid-range")

    print(f"\n[ITINERARY AGENT] Calling LLM to generate itinerary for '{destination}'...")

    prompt_config  = load_prompt("itinerary")
    system_message = prompt_config["system_message"]
    temperature    = prompt_config["temperature"]
    max_tokens     = prompt_config["max_tokens"]
    prompt_version = prompt_config["prompt_version"]

    feedback_section = ""
    if feedback and feedback.lower() not in ("approve", ""):
        feedback_section = f"\nIMPORTANT — incorporate this user feedback:\n{feedback}\n"

    user_prompt = f"""Create a detailed day-by-day travel itinerary for this trip.

TRIP DETAILS:
- Destination  : {destination}
- Dates        : {travel_dates}
- Travel style : {travel_style} (plan activities appropriate for a {travel_style} traveler)
- Flight       : {selected_flight.get('airline','N/A')} | Departs {selected_flight.get('departure','N/A')} | Arrives {selected_flight.get('arrival','N/A')}
- Hotel        : {selected_hotel.get('name','N/A')} in {selected_hotel.get('location','N/A')}
- Food budget  : Rs {budget.get('food_total',0):,} total
- Activities   : Rs {budget.get('activities_total',0):,} total

DESTINATION CONTEXT:
{dest_info}

TRAVEL TIPS TO INCORPORATE:
{tips}
{feedback_section}
FORMAT each day exactly like this:
DAY N — Weekday DD Mon  |  THEME
  HH:MM  Activity with specific names, costs in local currency, and tips

Rules:
- Day 1 must account for arrival time and travel fatigue
- Last day must include airport transfer with timing
- Include breakfast, lunch, dinner suggestions every day
- Mention specific attraction names, entry costs, booking tips
- Include one budget-saving tip per day
- Plain text only — no markdown, no bullet symbols"""

    result = call_llm_safe(
        prompt=user_prompt,
        system=system_message,
        agent_name="itinerary",
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
            "itinerary": prompt_version,
        },
    }

    if not result["success"]:
        return {**state, "error_message": result["error"], "status": "failed"}

    itinerary = result["content"].strip()

    if len(itinerary) < 200:
        raise ValueError(f"LLM returned suspiciously short itinerary ({len(itinerary)} chars)")

    print(f"  [OK] Itinerary generated ({len(itinerary.splitlines())} lines)")

    return {
        **state,
        "itinerary": itinerary,
        "status":    "itinerary",
    }
