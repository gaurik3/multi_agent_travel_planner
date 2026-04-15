from state import TravelPlanState

def checkpoint_1_node(state: TravelPlanState) -> TravelPlanState:
    options  = state.get("flight_options", [])
    feedback = state.get("human_feedback_1", "").strip().lower()

    print("\n" + "=" * 60)
    print("  CHECKPOINT 1 — FLIGHT SELECTION")
    print("=" * 60)

    for opt in options:
        print(f"\n  Option {opt['option']}: {opt['airline']}")
        print(f"  Route    : {opt['route']}")
        print(f"  Depart   : {opt['departure']}")
        print(f"  Arrive   : {opt['arrival']}")
        print(f"  Duration : {opt['duration']}")
        print(f"  Cost     : Rs {opt['total_price_inr']:,}  "
              f"(Rs {opt['price_per_person_inr']:,}/person)")
        print(f"  Pros     : {opt['pros']}")
        print(f"  Cons     : {opt['cons']}")
        print()

    if feedback == "reject":
        retry = state.get("retry_count", 0) + 1
        print(f"  [REJECTED] Requesting new flight options... (attempt {retry}/3)")
        print("=" * 60)
        return {
            **state,
            "flight_options": [],       
            "human_feedback_1": "",      
            "retry_count": retry,
            "status": "retry_flights",
        }

    choice_map = {str(opt["option"]): opt for opt in options}

    if feedback in choice_map:
        selected = choice_map[feedback]
        print(f"  [SELECTED] Option {feedback}: {selected['airline']}")
        print("=" * 60)
        return {
            **state,
            "selected_flight":  selected,
            "human_feedback_1": feedback,
            "status":           "checkpoint_1",
        }

    print(f"  [WARN] Unrecognised input '{feedback}' — defaulting to Option 1")
    selected = options[0] if options else {}
    print("=" * 60)
    return {
        **state,
        "selected_flight":  selected,
        "human_feedback_1": "1",
        "status":           "checkpoint_1",
    }