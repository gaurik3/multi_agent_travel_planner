import sys
import os
import uuid
import time
sys.path.insert(0, os.path.dirname(__file__))
from graph import app
from state import TravelPlanState
from utils.diagram import print_ascii_diagram, export_png_diagram
from utils.logger import init_db
from utils.cost_guard import format_cost_summary
from classifier.travel_style_classifier import classify_travel_style


def banner(title: str):
    W = 62
    print("\n" + "═" * W)
    print(f"  {title}")
    print("═" * W)


def get_next_nodes(config: dict) -> tuple:
    snapshot = app.get_state(config)
    return snapshot.next if snapshot else ()


def get_current_state(config: dict) -> dict:
    snapshot = app.get_state(config)
    return snapshot.values if snapshot else {}


def collect_trip_inputs() -> TravelPlanState:
    banner("MULTI-AGENT TRAVEL PLANNER  —  Powered by LangGraph + GPT-4o")
    print("  Answer the questions below to generate your complete travel plan.\n")

    destination = input("  Destination (e.g. Paris, France): ").strip()
    while not destination:
        destination = input("  Destination cannot be empty: ").strip()

    origin = input("  Origin city (e.g. New Delhi, India): ").strip()
    while not origin:
        origin = input("  Origin cannot be empty: ").strip()

    travel_dates = input("  Travel dates (e.g. 15 June 2025 to 25 June 2025): ").strip()
    while not travel_dates:
        travel_dates = input("  Dates cannot be empty: ").strip()

    while True:
        try:
            num_travelers = int(input("  Number of travellers: ").strip())
            if num_travelers < 1:
                raise ValueError
            break
        except ValueError:
            print("  Please enter a whole number (e.g. 2)")

    while True:
        try:
            budget_inr = float(input("  Total budget in INR (e.g. 200000): ").strip())
            if budget_inr <= 0:
                raise ValueError
            break
        except ValueError:
            print("  Please enter a positive number (e.g. 200000)")

    banner("TRIP SUMMARY")
    print(f"  Destination : {destination}")
    print(f"  Origin      : {origin}")
    print(f"  Dates       : {travel_dates}")
    print(f"  Travellers  : {num_travelers}")
    print(f"  Budget      : Rs {budget_inr:,.0f}")
    print("═" * 62)

    confirm = input("\n  Confirm and start planning? (yes/no): ").strip().lower()
    if confirm not in ("yes", "y"):
        print("  Cancelled. Restart to try again.")
        sys.exit(0)

    return destination, origin, travel_dates, num_travelers, budget_inr


def collect_flight_choice(state: dict) -> str:
    options = state.get("flight_options", [])

    print("\n" + "=" * 62)
    print("  CHECKPOINT 1 — SELECT YOUR FLIGHT")
    print("=" * 62)
    for opt in options:
        print(f"\n  Option {opt['option']}: {opt['airline']}")
        print(f"  Route    : {opt['route']}")
        print(f"  Departs  : {opt['departure']}")
        print(f"  Arrives  : {opt['arrival']}")
        print(f"  Duration : {opt['duration']}")
        print(f"  Cost     : Rs {opt['total_price_inr']:,}  "
              f"(Rs {opt['price_per_person_inr']:,}/person)")
        print(f"  Pros     : {opt['pros']}")
        print(f"  Cons     : {opt['cons']}")
        print()

    valid = {str(opt["option"]) for opt in options} | {"reject"}
    while True:
        choice = input(
            "  Enter 1, 2, or 3 to select a flight, "
            "or 'reject' for new options: "
        ).strip().lower()
        if choice in valid:
            return choice
        print(f"  Invalid — please enter one of: {', '.join(sorted(valid))}")


def collect_final_approval(state: dict) -> str:
    print("\n" + "=" * 62)
    print("  CHECKPOINT 2 — APPROVE YOUR PLAN")
    print("=" * 62)
    print("  Type 'approve' to accept and generate your final plan.")
    print("  Or describe changes  (e.g. 'more free time on day 3')")
    print("  To pick a specific hotel prefix with hotel:2")
    print()
    feedback = input("  Your response: ").strip()
    while not feedback:
        feedback = input("  Response cannot be empty: ").strip()
    return feedback


def main():
    # Initialise DB tables once at startup
    init_db()

    print_ascii_diagram(app)

    base_dir = os.path.dirname(os.path.abspath(__file__))
    png_path = os.path.join(base_dir, "graph_diagram.png")
    export_png_diagram(app, png_path)

    # Collect user inputs
    destination, origin, travel_dates, num_travelers, budget_inr = collect_trip_inputs()

    # Generate unique run_id
    run_id = str(uuid.uuid4())[:8]
    print(f"\n  Run ID: {run_id}")

    # Run travel style classifier (Module 6)
    classifier_result = classify_travel_style(
        budget_inr=budget_inr,
        num_travelers=num_travelers,
        travel_dates=travel_dates,
        destination=destination,
        run_id=run_id
    )
    print(f"\n  Travel style detected: {classifier_result['travel_style'].upper()}")
    print(f"  Budget per person/day : ₹{classifier_result['budget_per_person_per_day']:,.0f}")
    print(f"  Destination type      : {classifier_result['destination_type']}")

    thread_id = str(uuid.uuid4())
    config    = {"configurable": {"thread_id": thread_id}}

    initial_state = {
        "destination":          destination,
        "origin":               origin,
        "travel_dates":         travel_dates,
        "num_travelers":        num_travelers,
        "budget_inr":           budget_inr,
        "destination_info":     "",
        "visa_info":            "",
        "best_travel_tips":     "",
        "budget_breakdown":     {},
        "flight_options":       [],
        "selected_flight":      {},
        "hotel_options":        [],
        "selected_hotel":       {},
        "itinerary":            "",
        "validation_notes":     "",
        "human_feedback_1":     "",
        "human_feedback_2":     "",
        "status":               "",
        "retry_count":          0,
        "error_message":        "",
        "failure_type":         "",
        "final_plan":           "",
        "run_id":               run_id,
        "total_tokens_in":      0,
        "total_tokens_out":     0,
        "total_cost_usd":       0.0,
        "prompt_versions_used": {},
        "travel_style":         classifier_result["travel_style"],
    }

    print("\n  ▶  Agents are working on your plan...\n")

    run_start = time.time()
    app.invoke(initial_state, config=config)

    while "checkpoint_1" in get_next_nodes(config):
        current_state = get_current_state(config)

        if current_state.get("status") == "failed":
            print("\n    Planning failed. See error above.")
            return

        if current_state.get("retry_count", 0) >= 3:
            print("\n    Too many retries on flight selection.")
            return

        choice = collect_flight_choice(current_state)
        app.update_state(config, {"human_feedback_1": choice})
        app.invoke(None, config=config)

    while "checkpoint_2" in get_next_nodes(config):
        current_state = get_current_state(config)

        if current_state.get("status") == "failed":
            print("\n    Planning failed. See error above.")
            return

        if current_state.get("retry_count", 0) >= 3:
            print("\n    Too many retries on plan approval.")
            return

        feedback = collect_final_approval(current_state)
        app.update_state(config, {"human_feedback_2": feedback})
        app.invoke(None, config=config)

    final_state = get_current_state(config)

    if final_state.get("status") == "failed":
        print("\n    Planning failed. See error above.")
        return

    banner("YOUR TRAVEL PLAN IS COMPLETE  ")
    print(f"  Thread ID : {thread_id}")
    print(f"  Run ID    : {run_id}")
    print(f"  The plan has been printed above and saved to a .txt file")
    print(f"  Graph diagram saved to: graph_diagram.png\n")

    # Print cost summary
    print(format_cost_summary(
        final_state.get("total_tokens_in", 0),
        final_state.get("total_tokens_out", 0)
    ))


if __name__ == "__main__":
    main()
