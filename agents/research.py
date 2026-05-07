import json
from state import TravelPlanState
from utils.llm import call_llm_safe
from utils.error_handler import safe_node
from utils.prompt_loader import load_prompt


@safe_node
def research_node(state: TravelPlanState) -> TravelPlanState:
    destination   = state["destination"]
    travel_dates  = state["travel_dates"]
    num_travelers = state["num_travelers"]

    print(f"\n[RESEARCH AGENT] Calling LLM for '{destination}'...")

    prompt_config  = load_prompt("research")
    system_message = prompt_config["system_message"]
    temperature    = prompt_config["temperature"]
    max_tokens     = prompt_config["max_tokens"]
    prompt_version = prompt_config["prompt_version"]

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

    result = call_llm_safe(
        prompt=user_prompt,
        system=system_message,
        agent_name="research",
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
            "research": prompt_version,
        },
    }

    if not result["success"]:
        return {**state, "error_message": result["error"], "status": "failed"}

    raw   = result["content"]
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
