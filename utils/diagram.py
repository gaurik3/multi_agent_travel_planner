import os
import sys
import textwrap
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch

def print_ascii_diagram(app):
    W = 60
    print("\n" + "═" * W)
    print("  GRAPH DIAGRAM (ASCII)")
    print("═" * W)
    try:
        print(app.get_graph().draw_ascii())
    except Exception as e:
        print(f"  (grandalf not installed — run: pip install grandalf)\n  Error: {e}")
    print("═" * W + "\n")


def export_png_diagram(app, output_path: str = "graph_diagram.png"):
    try:
        _render_png(app, output_path)
        print(f"  [OK] Graph diagram saved → {output_path}")
    except Exception as e:
        print(f"  [WARN] Could not export PNG diagram: {e}")


def _render_png(app, output_path: str):
    nodes = [
        ("__start__",    0.50, 0.95, "START",        "#e8f5e9"),
        ("orchestrator", 0.50, 0.83, "orchestrator",  "#e3f2fd"),
        ("research",     0.10, 0.68, "research",       "#f3e5f5"),
        ("budget",       0.28, 0.68, "budget",         "#f3e5f5"),
        ("flights",      0.46, 0.68, "flights",        "#f3e5f5"),
        ("checkpoint_1", 0.46, 0.53, "checkpoint_1\n(interrupt)",  "#fff9c4"),
        ("hotels",       0.64, 0.68, "hotels",         "#f3e5f5"),
        ("itinerary",    0.74, 0.53, "itinerary",      "#f3e5f5"),
        ("validate",     0.74, 0.38, "validate",       "#f3e5f5"),
        ("checkpoint_2", 0.74, 0.23, "checkpoint_2\n(interrupt)",  "#fff9c4"),
        ("final_plan",   0.50, 0.10, "final_plan",     "#e8f5e9"),
        ("failed",       0.10, 0.10, "failed\n(safe exit)", "#ffebee"),
        ("__end__",      0.50, -0.02, "END",           "#e8f5e9"),
    ]

    node_pos   = {n[0]: (n[1], n[2]) for n in nodes}
    node_label = {n[0]: n[3] for n in nodes}
    node_color = {n[0]: n[4] for n in nodes}

    edges = [
        ("__start__",    "orchestrator"),
        ("orchestrator", "research"),
        ("orchestrator", "budget"),
        ("orchestrator", "flights"),
        ("orchestrator", "checkpoint_1"),
        ("orchestrator", "hotels"),
        ("orchestrator", "itinerary"),
        ("orchestrator", "validate"),
        ("orchestrator", "checkpoint_2"),
        ("orchestrator", "final_plan"),
        ("orchestrator", "failed"),
        ("orchestrator", "__end__"),
        ("research",     "orchestrator"),
        ("budget",       "orchestrator"),
        ("flights",      "orchestrator"),
        ("checkpoint_1", "orchestrator"),
        ("hotels",       "orchestrator"),
        ("itinerary",    "orchestrator"),
        ("validate",     "orchestrator"),
        ("checkpoint_2", "orchestrator"),
        ("final_plan",   "__end__"),
        ("failed",       "__end__"),
    ]

    fig, ax = plt.subplots(figsize=(14, 10))
    ax.set_xlim(-0.05, 1.05)
    ax.set_ylim(-0.08, 1.05)
    ax.axis("off")
    fig.patch.set_facecolor("#fafafa")

    for src, dst in edges:
        x1, y1 = node_pos[src]
        x2, y2 = node_pos[dst]
        ax.annotate(
            "",
            xy=(x2, y2), xytext=(x1, y1),
            arrowprops=dict(
                arrowstyle="->",
                color="#90a4ae",
                lw=1.2,
                connectionstyle="arc3,rad=0.08",
            ),
        )

    for node_id, x, y, label, color in nodes:
        lines    = label.split("\n")
        height   = 0.055 + 0.022 * (len(lines) - 1)
        width    = max(len(l) for l in lines) * 0.012 + 0.04

        box = FancyBboxPatch(
            (x - width / 2, y - height / 2),
            width, height,
            boxstyle="round,pad=0.01",
            linewidth=1.2,
            edgecolor="#546e7a",
            facecolor=color,
            zorder=3,
        )
        ax.add_patch(box)
        ax.text(
            x, y, label,
            ha="center", va="center",
            fontsize=7.5, fontweight="bold",
            color="#1a1a2e", zorder=4,
            multialignment="center",
        )

    legend_handles = [
        mpatches.Patch(color="#f3e5f5", label="Agent nodes"),
        mpatches.Patch(color="#fff9c4", label="Human checkpoints (interrupt)"),
        mpatches.Patch(color="#e3f2fd", label="Orchestrator"),
        mpatches.Patch(color="#ffebee", label="Safe exit"),
        mpatches.Patch(color="#e8f5e9", label="Start / End"),
    ]
    ax.legend(handles=legend_handles, loc="lower right",
              fontsize=8, framealpha=0.9)

    ax.set_title(
        "Multi-Agent Travel Planner — LangGraph",
        fontsize=13, fontweight="bold", pad=12, color="#1a1a2e",
    )

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    plt.close()