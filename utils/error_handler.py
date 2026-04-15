import functools
import traceback
from state import TravelPlanState

def safe_node(fn):
    @functools.wraps(fn)
    def wrapper(state: TravelPlanState) -> TravelPlanState:
        try:
            return fn(state)
        except Exception as e:
            # Full traceback to terminal so the developer can see what happened
            print(f"\n[ERROR] Unhandled exception in node '{fn.__name__}':")
            traceback.print_exc()
            return {
                **state,
                "error_message": f"{fn.__name__} crashed: {type(e).__name__}: {e}",
                "status": "failed",
            }
    return wrapper