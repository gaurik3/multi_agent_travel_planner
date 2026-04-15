from state import TravelPlanState

def checkpoint_2_node(state: TravelPlanState) -> TravelPlanState:
    options  = state.get("hotel_options", [])
    feedback = state.get("human_feedback_2", "").strip()

    print("\n" + "=" * 60)
    print("  CHECKPOINT 2 — HOTEL SELECTION & FINAL PLAN APPROVAL")
    print("=" * 60)

    print("\n  --- HOTEL OPTIONS ---")
    for opt in options:
        print(f"\n  Option {opt['option']}: {opt['name']}  ({opt['stars']}★)")
        print(f"  Location  : {opt['location']}")
        print(f"  Check-in  : {opt['check_in']}  →  Check-out : {opt['check_out']}")
        print(f"  Cost      : Rs {opt['total_price_inr']:,}  "
              f"(Rs {opt['price_per_night_inr']:,}/night)")
        print(f"  Pros      : {opt['pros']}")
        print(f"  Cons      : {opt['cons']}")

    print("\n  --- YOUR ITINERARY ---")
    itinerary = state.get("itinerary", "No itinerary generated.")
    for line in itinerary.splitlines():
        print(f"  {line}")

    print("\n  --- VALIDATION ---")
    print(f"  {state.get('validation_notes', 'N/A')}")
    print()


    selected_hotel = options[0] if options else {}   # default: option 1

    feedback_lower = feedback.lower()

    for opt in options:
        if f"hotel:{opt['option']}" in feedback_lower:
            selected_hotel = opt
            break

    if feedback_lower == "approve" or feedback_lower.startswith("approve"):
        print(f"  [APPROVED] Hotel selected: {selected_hotel['name']}")
        print("=" * 60)
        return {
            **state,
            "selected_hotel":   selected_hotel,
            "human_feedback_2": feedback,
            "status":           "checkpoint_2",
        }

    retry = state.get("retry_count", 0) + 1
    print(f"  [CHANGE REQUESTED] Re-generating itinerary with feedback... "
          f"(attempt {retry}/3)")
    print(f"  Feedback: {feedback}")
    print("=" * 60)
    return {
        **state,
        "selected_hotel":   selected_hotel,
        "itinerary":        "",           
        "validation_notes": "",          
        "human_feedback_2": feedback,     
        "retry_count":      retry,
        "status":           "retry_itinerary",
    }