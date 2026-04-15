import json
from state import TravelPlanState
from utils.llm import call_llm_safe
from utils.error_handler import safe_node

SYSTEM = """You are an expert travel researcher with deep knowledge of destinations
worldwide, visa requirements for Indian passport holders, and practical travel tips.
Always respond with valid JSON only — no markdown fences, no extra text."""

@safe_node
def research_node(state: TravelPlanState) -> TravelPlanState:
    destination   = state["destination"]
    travel_dates  = state["travel_dates"]
    num_travelers = state["num_travelers"]

    print(f"\n[RESEARCH AGENT] Calling LLM for '{destination}'...")

    user_prompt = f"""Research this trip and return a JSON object with exactly these three keys:

Destination : {destination}
Travel dates: {travel_dates}
Travellers  : {num_travelers}

Return this exact JSON structure:
{{
  "destination_info": "3-4 sentences: what the destination is known for, best things to do, ideal travel season, local transport",
  "visa_info": "Visa requirements for Indian passport holders: type, where to apply, documents, fees in INR, processing time",
  "best_travel_tips": "8 practical numbered tips: money, transport, food, safety, cultural etiquette, booking advice"
}}

Return only the JSON object. No markdown, no explanation."""

    raw   = call_llm_safe(SYSTEM, user_prompt)
    clean = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    data  = json.loads(clean)

    for key in ("destination_info", "visa_info", "best_travel_tips"):
        if not data.get(key):
            raise ValueError(f"LLM returned empty field: {key}")

    print(f"  [OK] Research complete ({len(data['destination_info'])} chars)")

    return {
        **state,
        "destination_info": data["destination_info"],
        "visa_info":        data["visa_info"],
        "best_travel_tips": data["best_travel_tips"],
        "status":           "research",
    }