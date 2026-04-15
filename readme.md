# ✈ Multi-Agent Travel Planner

A Python application that takes your travel inputs and produces a complete, human-approved travel plan — built as a learning project for **LangGraph multi-agent workflows**.

---

## What This Project Does

You type in a destination, origin, dates, number of travellers, and budget. Seven AI agents then work in sequence — each doing one specific job — and the result is a full travel plan including flight options, hotel options, a day-by-day itinerary, budget breakdown, visa info, and travel tips.

The graph pauses **twice** for your input: once to let you pick a flight, and once to approve (or request changes to) the final itinerary. If you reject a flight or ask for changes, the relevant agent re-runs automatically. After three failed retries, the graph exits cleanly with a helpful error message.

---

## Architecture

```
User Input
    │
    ▼
┌─────────────────────────────────────────────────────────┐
│                      ORCHESTRATOR                       │
│          (no LLM — pure routing logic)                  │
└────────────┬────────────────────────────────────────────┘
             │ reads state["status"], decides next node
             ▼
    ┌────────────────┐
    │    research    │  ← destination info, visa, tips
    └───────┬────────┘
            ▼
    ┌────────────────┐
    │     budget     │  ← INR breakdown across categories
    └───────┬────────┘
            ▼
    ┌────────────────┐
    │    flights     │  ← 3 realistic flight options
    └───────┬────────┘
            ▼
    ┌────────────────┐
    │  checkpoint_1  │  ← ⏸ PAUSE: you pick a flight
    └───────┬────────┘
            ▼
    ┌────────────────┐
    │     hotels     │  ← 3 hotel options
    └───────┬────────┘
            ▼
    ┌────────────────┐
    │   itinerary    │  ← day-by-day plan with times
    └───────┬────────┘
            ▼
    ┌────────────────┐
    │    validate    │  ← checks dates, budget, conflicts
    └───────┬────────┘
            ▼
    ┌────────────────┐
    │  checkpoint_2  │  ← ⏸ PAUSE: you approve or request changes
    └───────┬────────┘
            ▼
    ┌────────────────┐
    │   final_plan   │  ← formatted plan printed + saved to .txt
    └───────┬────────┘
            ▼
           END
```

If any agent fails or retries exceed 3, the graph routes to a **safe exit node** that prints a clean error message instead of crashing.

---

## Project Structure

```
travel-planner/
├── .env                        ← your Azure OpenAI credentials (never commit this)
├── requirements.txt
├── main.py                     ← entry point — run this
├── state.py                    ← TravelPlanState TypedDict (shared across all nodes)
├── graph.py                    ← graph assembly + MemorySaver compilation
│
├── agents/
│   ├── orchestrator.py         ← routing logic + retry_count guard
│   ├── research.py             ← destination info, visa, tips
│   ├── budget.py               ← INR budget breakdown
│   ├── flights.py              ← 3 flight options (LLM-generated)
│   ├── hotels.py               ← 3 hotel options (LLM-generated)
│   ├── itinerary.py            ← day-by-day plan
│   └── validator.py            ← local checks + LLM deep review
│
├── checkpoints/
│   ├── checkpoint_1.py         ← flight selection HITL node
│   └── checkpoint_2.py         ← final approval HITL node
│
└── utils/
    ├── llm.py                  ← AzureChatOpenAI init + call_llm_safe() with retry
    ├── error_handler.py        ← @safe_node decorator for all agents
    ├── safe_exit.py            ← safe exit node
    ├── final_plan.py           ← formatter + .txt file save
    └── diagram.py              ← ASCII terminal diagram + PNG export
```

---

## Tech Stack

| Component | Technology |
|---|---|
| Agent orchestration | LangGraph >= 0.2.0 |
| LLM | Azure OpenAI — GPT-4o |
| LLM client | LangChain + langchain-openai |
| State persistence | LangGraph MemorySaver (in-memory) |
| Retry logic | tenacity (exponential backoff) |
| Graph diagram | grandalf (ASCII) + matplotlib (PNG) |
| Environment vars | python-dotenv |
| Python | 3.11+ |

Flight and hotel data is **LLM-generated** (realistic but not from a live booking API) — this is intentional for a learning project.

---

## Setup

### 1. Prerequisites

- Python 3.11 or higher
- An Azure OpenAI resource with a GPT-4o deployment
- The four Azure credentials from your Azure portal

### 2. Clone / download the project

```
travel-planner/
└── (all files as shown in the structure above)
```

### 3. Create a virtual environment

```bash
python -m venv venv

# Mac / Linux
source venv/bin/activate

# Windows (PowerShell — run this first if you get an execution policy error)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
venv\Scripts\activate

# Windows (Command Prompt)
venv\Scripts\activate.bat
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Create your `.env` file

Create a file called `.env` in the project root (same folder as `main.py`) with your Azure OpenAI credentials:

```
AZURE_OPENAI_ENDPOINT=https://your-resource-name.openai.azure.com
AZURE_OPENAI_DEPLOYMENT=gpt-4o
AZURE_OPENAI_API_KEY=your-api-key-here
AZURE_OPENAI_API_VERSION=2024-12-01-preview
```

> **Important:** No spaces around `=`. No quotes around values. Never commit this file to git.

---

## Running the Planner

```bash
python main.py
```

You will be asked for:

```
Destination (e.g. Paris, France): Dubai
Origin city (e.g. New Delhi, India): New Delhi
Travel dates (e.g. 15 June 2025 to 25 June 2025): 30 July 2026 to 5 August 2026
Number of travellers: 2
Total budget in INR (e.g. 200000): 200000
```

The agents then run in sequence. You will be prompted **twice**:

**Checkpoint 1 — Flight selection:**
```
Enter 1, 2, or 3 to select a flight, or 'reject' for new options: 1
```

**Checkpoint 2 — Final approval:**
```
Type 'approve' to accept this plan.
Or describe what you'd like changed (e.g. 'more free time on day 3')

Your response: approve
```

On completion, the full plan is:
- Printed to the terminal
- Saved automatically as `travel_plan_Dubai_20260730_143022.txt` in the project folder
- The graph diagram is saved as `graph_diagram.png`

---

## How the State Works

Every node reads from and writes to a single shared `TravelPlanState` TypedDict. LangGraph passes it between nodes automatically — no agent ever calls another agent directly.

```python
class TravelPlanState(TypedDict):
    # User inputs
    destination: str
    origin: str
    travel_dates: str
    num_travelers: int
    budget_inr: float

    # Filled in progressively by agents
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

    # Human interaction
    human_feedback_1: str    # "1" / "2" / "3" / "reject"
    human_feedback_2: str    # "approve" or change description

    # Control flow
    status: str              # routing signal read by orchestrator
    retry_count: int         # incremented on each retry, exits at >= 3
    error_message: str       # set when an agent fails

    # Output
    final_plan: str
```

---

## Error Handling

Three strategies work together to guarantee the graph always terminates cleanly:

**1. Retry with backoff** (`utils/llm.py`)
The `@retry` decorator on `call_llm_safe()` handles transient API errors (`RateLimitError`, `APITimeoutError`, `APIConnectionError`) automatically — waits 2s, 4s, 8s before giving up.

**2. `@safe_node` decorator** (`utils/error_handler.py`)
Wraps every agent function. If anything raises an unexpected exception (bad JSON, missing key, empty response), the decorator catches it, prints the full traceback, sets `error_message` in state, and sets `status = "failed"` so the orchestrator routes to `safe_exit_node` instead of crashing Python.

**3. `retry_count` guard** (`agents/orchestrator.py`)
Every retry path increments `state["retry_count"]`. The orchestrator checks this first on every invocation. At `>= 3` it routes to `failed` regardless of what else is happening — guaranteeing no infinite loops.

---

## Human-in-the-Loop (How the Pausing Works)

LangGraph's `interrupt_before` mechanism is used with a `MemorySaver` checkpointer:

```python
app = builder.compile(
    checkpointer=MemorySaver(),
    interrupt_before=["checkpoint_1", "checkpoint_2"],
)
```

When the graph reaches `checkpoint_1` or `checkpoint_2`, it **pauses before running that node** and returns control to `main.py`. The main loop then:

1. Reads the current state with `app.get_state(config)`
2. Displays the options to the user
3. Collects input via `input()`
4. Writes the feedback into state with `app.update_state(config, {...})`
5. Resumes the graph with `app.invoke(None, config=config)`

The `thread_id` in `config` is what ties all the resume calls to the same run — LangGraph uses it to look up the saved state in MemorySaver.

---

## Key Concepts Demonstrated

| Concept | Where |
|---|---|
| StateGraph with TypedDict | `state.py`, `graph.py` |
| Conditional edges | `graph.py` → `route_by_status()` |
| Human-in-the-loop with interrupt | `graph.py`, `main.py`, `checkpoints/` |
| MemorySaver checkpointer | `graph.py` |
| Multi-agent routing via shared state | `agents/orchestrator.py` |
| Retry loops with state mutation | `checkpoints/checkpoint_1.py` |
| Structured LLM output (JSON parsing) | All agents |
| Error handling with graceful exit | `utils/error_handler.py`, `utils/safe_exit.py` |
| Tenacity retry decorator | `utils/llm.py` |

---

## Development Phases

This project was built in 6 phases as a learning exercise:

| Phase | What was built |
|---|---|
| 1 | Skeleton — all nodes as stubs, graph wired and running end-to-end |
| 2 | Mock data — realistic hardcoded data, no LLM, full state flow verified |
| 3 | Real LLM — Azure OpenAI GPT-4o calls, JSON parsing, per-agent error handling |
| 4 | Human-in-the-loop — MemorySaver, interrupt_before, CLI pause/resume |
| 5 | Error handling — @safe_node decorator, retry_count guard, safe exit |
| 6 | Polish — ASCII + PNG diagram, enriched formatter, auto .txt save |

---

## Sample Output

```
══════════════════════════════════════════════════════════════
  ✈  TRAVEL PLAN  —  DUBAI
  Generated: 30 Jul 2026, 14:30
══════════════════════════════════════════════════════════════
  TRIP AT A GLANCE
──────────────────────────────────────────────────────────────
  Destination  :  Dubai
  Origin       :  New Delhi
  Dates        :  30 July 2026 to 5 August 2026
  Travellers   :  2
  Budget       :  Rs 200,000
──────────────────────────────────────────────────────────────
  SELECTED FLIGHT
──────────────────────────────────────────────────────────────
  Airline   :  IndiGo 6E-148
  Route     :  DEL -> DXB (non-stop)
  Departs   :  30 Jul 2026, 06:00 (DEL)
  Arrives   :  30 Jul 2026, 08:30 (DXB)
  Cost      :  Rs 36,000  (Rs 18,000 / person)
──────────────────────────────────────────────────────────────
  BUDGET BREAKDOWN
──────────────────────────────────────────────────────────────
  Flights (per person)  :  Rs 18,000
  Hotels (total)        :  Rs 75,000
  Food (total)          :  Rs 20,000
  Activities (total)    :  Rs 18,000
  Buffer                :  Rs 10,000
──────────────────────────────────────────────────────────────
  ESTIMATED TOTAL       :  Rs 159,000  of Rs 200,000 budget
  [████████████████████████████████████░░░░░░░░░░] 80%
...
```

---

## Notes

- **Flight and hotel data is LLM-generated**, not from a live API. Prices and timings are realistic but fictional — always verify on an actual booking platform before purchasing.
- **MemorySaver is in-memory only** — state is lost when the program exits. For a production version, replace with `SqliteSaver` or `PostgresSaver`.
- The `.env` file must never be committed to version control. Add it to `.gitignore`.