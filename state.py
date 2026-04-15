from typing import TypedDict, Any


class TravelPlanState(TypedDict):
    destination: str
    origin: str
    travel_dates: str
    num_travelers: int
    budget_inr: float
    destination_info: str
    visa_info: str
    best_travel_tips: str
    budget_breakdown: dict
    flight_options: list
    selected_flight: dict
    hotel_options: list
    selected_hotel: dict
    itinerary: str
    validation_notes: str
    human_feedback_1: str   
    human_feedback_2: str   
    status: str             
    retry_count: int        
    error_message: str     
    final_plan: str         