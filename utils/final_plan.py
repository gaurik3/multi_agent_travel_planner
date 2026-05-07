import os
from datetime import datetime
from state import TravelPlanState
from utils.logger import persist_run_record


def generate_final_plan(state: TravelPlanState) -> str:
    sf  = state.get("selected_flight", {})
    sh  = state.get("selected_hotel", {})
    bd  = state.get("budget_breakdown", {})

    W     = 62
    thick = "═" * W
    thin  = "─" * W
    now   = datetime.now().strftime("%d %b %Y, %H:%M")

    def section(title: str) -> list:
        return [thin, f"  {title}", thin]

    def money(amount) -> str:
        try:
            return f"Rs {int(amount):,}"
        except (TypeError, ValueError):
            return "Rs N/A"

    lines = [
        "",
        thick,
        f"  ✈  TRAVEL PLAN  —  {state.get('destination', '').upper()}",
        f"  Generated: {now}",
        thick,
        "",
        *section("TRIP AT A GLANCE"),
        f"  Destination  :  {state.get('destination', 'N/A')}",
        f"  Origin       :  {state.get('origin', 'N/A')}",
        f"  Dates        :  {state.get('travel_dates', 'N/A')}",
        f"  Travellers   :  {state.get('num_travelers', 'N/A')}",
        f"  Budget       :  {money(state.get('budget_inr', 0))}",
        f"  Travel Style :  {state.get('travel_style', 'N/A').upper()}",
        f"  Run ID       :  {state.get('run_id', 'N/A')}",
        "",
        *section("DESTINATION OVERVIEW"),
        _wrap(state.get("destination_info", "N/A"), W - 4),
        "",
        *section("VISA INFORMATION"),
        _wrap(state.get("visa_info", "N/A"), W - 4),
        "",
        *section("TRAVEL TIPS"),
        _wrap(state.get("best_travel_tips", "N/A"), W - 4),
        "",
        *section("SELECTED FLIGHT"),
        f"  Airline   :  {sf.get('airline', 'N/A')}",
        f"  Route     :  {sf.get('route', 'N/A')}",
        f"  Departs   :  {sf.get('departure', 'N/A')}",
        f"  Arrives   :  {sf.get('arrival', 'N/A')}",
        f"  Duration  :  {sf.get('duration', 'N/A')}",
        f"  Cost      :  {money(sf.get('total_price_inr', 0))}  "
        f"({money(sf.get('price_per_person_inr', 0))} / person)",
        "",
        *section("SELECTED HOTEL"),
        f"  Name      :  {sh.get('name', 'N/A')}  ({sh.get('stars', '?')}★)",
        f"  Location  :  {sh.get('location', 'N/A')}",
        f"  Check-in  :  {sh.get('check_in', 'N/A')}",
        f"  Check-out :  {sh.get('check_out', 'N/A')}",
        f"  Cost      :  {money(sh.get('total_price_inr', 0))}  "
        f"({money(sh.get('price_per_night_inr', 0))} / night)",
        "",
        *section("BUDGET BREAKDOWN"),
        f"  Flights (per person)  :  {money(bd.get('flights_per_person', 0))}",
        f"  Hotels (total)        :  {money(bd.get('hotels_total', 0))}",
        f"  Food (total)          :  {money(bd.get('food_total', 0))}",
        f"  Activities (total)    :  {money(bd.get('activities_total', 0))}",
        f"  Buffer                :  {money(bd.get('buffer', 0))}",
        thin,
        f"  ESTIMATED TOTAL       :  {money(bd.get('total', 0))}  "
        f"of {money(state.get('budget_inr', 0))} budget",
        "",
        _budget_bar(bd.get("total", 0), state.get("budget_inr", 1), W - 4),
        "",
        *section("BUDGET NOTES"),
        _wrap(bd.get("notes", "N/A"), W - 4),
        "",
        *section("DAY-BY-DAY ITINERARY"),
        state.get("itinerary", "N/A"),
        "",
        *section("VALIDATION SUMMARY"),
        _wrap(state.get("validation_notes", "N/A"), W - 4),
        "",
        *section("LLM USAGE SUMMARY"),
        f"  Prompt versions : {state.get('prompt_versions_used', {})}",
        f"  Tokens in       : {state.get('total_tokens_in', 0):,}",
        f"  Tokens out      : {state.get('total_tokens_out', 0):,}",
        f"  Est. cost       : ${state.get('total_cost_usd', 0.0):.4f} USD",
        "",
        thick,
        "    Plan complete. Have a wonderful trip!",
        thick,
    ]

    return "\n".join(lines)


def _wrap(text: str, width: int) -> str:
    if not text:
        return "  N/A"
    import textwrap
    wrapped = textwrap.fill(text, width=width, initial_indent="  ",
                            subsequent_indent="  ")
    return wrapped


def _budget_bar(spent: float, total: float, width: int) -> str:
    try:
        ratio    = min(spent / total, 1.0)
        bar_w    = width - 12
        filled   = int(ratio * bar_w)
        empty    = bar_w - filled
        pct      = ratio * 100
        color    = "█" if pct <= 90 else "▓"
        bar      = color * filled + "░" * empty
        return f"  [{bar}] {pct:.0f}%"
    except (ZeroDivisionError, TypeError):
        return ""


def save_plan_to_file(plan: str, destination: str) -> str:
    safe_dest = "".join(c if c.isalnum() or c in " _-" else "_"
                        for c in destination).strip().replace(" ", "_")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename  = f"travel_plan_{safe_dest}_{timestamp}.txt"

    base_dir  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    filepath  = os.path.join(base_dir, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(plan)

    return filepath


def final_plan_node(state: TravelPlanState) -> TravelPlanState:
    print("\n[FINAL PLAN] Generating formatted travel plan...")

    plan = generate_final_plan(state)
    print(plan)

    # Persist success record to SQLite
    try:
        persist_run_record(
            run_id=state.get("run_id", "unknown"),
            destination=state.get("destination", ""),
            status="completed",
            failure_type=None,
            exit_reason=None,
            total_tokens=state.get("total_tokens_in", 0) + state.get("total_tokens_out", 0),
            total_cost_usd=state.get("total_cost_usd", 0.0),
            duration_seconds=0.0
        )
    except Exception as e:
        print(f"\n  [WARN] Could not persist run record: {e}")

    # Save to file automatically
    try:
        filepath = save_plan_to_file(plan, state.get("destination", "trip"))
        print(f"\n    Plan saved to: {filepath}")
    except Exception as e:
        print(f"\n  [WARN] Could not save plan to file: {e}")

    return {**state, "final_plan": plan, "status": "final_plan"}
