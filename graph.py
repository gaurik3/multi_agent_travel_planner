import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver
from state import TravelPlanState
from agents.orchestrator      import orchestrator_node, route_by_status
from agents.research          import research_node
from agents.budget            import budget_node
from agents.flights           import flights_node
from agents.hotels            import hotels_node
from agents.itinerary         import itinerary_node
from agents.validator         import validator_node
from checkpoints.checkpoint_1 import checkpoint_1_node
from checkpoints.checkpoint_2 import checkpoint_2_node
from utils.safe_exit          import safe_exit_node
from utils.final_plan         import final_plan_node

def build_graph(use_checkpointer: bool = True):
    builder = StateGraph(TravelPlanState)

    builder.add_node("orchestrator",  orchestrator_node)
    builder.add_node("research",      research_node)
    builder.add_node("budget",        budget_node)
    builder.add_node("flights",       flights_node)
    builder.add_node("checkpoint_1",  checkpoint_1_node)
    builder.add_node("hotels",        hotels_node)
    builder.add_node("itinerary",     itinerary_node)
    builder.add_node("validate",      validator_node)
    builder.add_node("checkpoint_2",  checkpoint_2_node)
    builder.add_node("final_plan",    final_plan_node)
    builder.add_node("failed",        safe_exit_node)

    builder.set_entry_point("orchestrator")

    builder.add_conditional_edges(
        "orchestrator",
        route_by_status,
        {
            "research":      "research",
            "budget":        "budget",
            "flights":       "flights",
            "checkpoint_1":  "checkpoint_1",
            "hotels":        "hotels",
            "itinerary":     "itinerary",
            "validate":      "validate",
            "checkpoint_2":  "checkpoint_2",
            "final_plan":    "final_plan",
            "failed":        "failed",
            "end":           END,
        },
    )

    for node_name in [
        "research", "budget", "flights",
        "checkpoint_1", "hotels", "itinerary",
        "validate", "checkpoint_2",
    ]:
        builder.add_edge(node_name, "orchestrator")

    builder.add_edge("final_plan", END)
    builder.add_edge("failed",     END)

    if use_checkpointer:
        import sqlite3
        DB_PATH = os.path.join(os.path.dirname(__file__), "data", "runs.db")
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        checkpointer = SqliteSaver(conn)
        app = builder.compile(
            checkpointer=checkpointer,
            interrupt_before=["checkpoint_1", "checkpoint_2"],
        )
        print("[GRAPH] Compiled with SqliteSaver + interrupt_before checkpoints")
    else:
        app = builder.compile()
        print("[GRAPH] Compiled without checkpointer")

    return app


app = build_graph(use_checkpointer=True)