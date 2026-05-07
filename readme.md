# ✈️ Multi-Agent Travel Planner

> A production-grade AI travel planning system built with LangGraph, powered by Azure OpenAI GPT-4o. It orchestrates a team of specialized agents to research destinations, plan budgets, find flights and hotels, craft day-by-day itineraries, and validate the complete plan — all with human-in-the-loop checkpoints, full observability, and cost guardrails.

---

## 📋 Table of Contents

- [What This Project Does](#what-this-project-does)
- [Capabilities](#capabilities)
- [Architecture](#architecture)
- [Agent Pipeline](#agent-pipeline)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Setup & Installation](#setup--installation)
- [Configuration](#configuration)
- [Running the Planner](#running-the-planner)
- [Modules Overview](#modules-overview)
- [Observability & Logs](#observability--logs)
- [Cost Guardrails](#cost-guardrails)
- [Prompt Versioning](#prompt-versioning)
- [Travel Style Classifier](#travel-style-classifier)

---

## What This Project Does

The Multi-Agent Travel Planner takes your destination, travel dates, number of travellers, and budget — then autonomously coordinates a pipeline of AI agents to produce a complete, validated travel plan. It pauses at two human checkpoints so you can select your preferred flight and approve (or request changes to) the itinerary before the final plan is generated and saved.

---

## Capabilities

### 🤖 Multi-Agent Orchestration
Six specialized agents each own one domain of travel planning. An **Orchestrator** routes between them based on state, retries, and cost/retry guardrails. No agent does more than its job.

### 🗺️ End-to-End Plan Generation
From a single prompt, the system produces:
- A destination overview, visa requirements for Indian passport holders, and practical travel tips
- A realistic budget breakdown across flights, hotels, food, activities, and a buffer
- Three realistic flight options with pros, cons, prices, and timings
- Three hotel options at different price points with check-in/out dates
- A detailed day-by-day itinerary with specific attraction names, costs in local currency, meal suggestions, and timing
- A validation pass checking for scheduling conflicts, budget overruns, and date mismatches

### 🧑‍💻 Human-in-the-Loop Checkpoints
The graph **interrupts** at two points and waits for human input before continuing:
- **Checkpoint 1** — You choose a flight option (or reject all and get new ones)
- **Checkpoint 2** — You review the full itinerary, select a hotel, and approve or request changes. The itinerary regenerates with your feedback incorporated.

### 🔁 Retry & Feedback Loops
If you reject flight options or request itinerary changes, the relevant agent reruns (up to 3 times) incorporating your feedback before re-presenting options.

### 🏷️ Travel Style Classification
Before the pipeline starts, a lightweight classifier analyses your budget-per-person-per-day and destination type to label the trip as **budget**, **mid-range**, **luxury**, or **adventure**. This label is passed to the itinerary agent to calibrate recommendations appropriately.

### 📊 Full Observability
Every LLM call is logged to a local SQLite database with: agent name, prompt version, token counts (in/out), latency in ms, cost in USD, retry count, and success/failure. Two CLI scripts let you inspect any run or list all past runs.

### 💰 Cost Guardrails
Hard token caps per agent and a soft USD cap per full run prevent runaway spending. The orchestrator checks both limits before routing to the next agent and short-circuits to a safe exit if either is breached.

### 🔖 Prompt Versioning
Every agent's system prompt lives in a versioned YAML file under `prompts/<agent>/v1.yaml`. Swapping to a new prompt version requires no code changes — just add a `v2.yaml`. The active version used in each run is recorded in state and printed in the final plan.

### 🛡️ Typed Failure Handling
When the pipeline fails, a `FailureClassifier` inspects the error and assigns one of six typed failure categories (`api_failure`, `prompt_parse_failure`, `validation_conflict`, `human_rejection`, `retry_exhaustion`, `cost_limit_exceeded`) before persisting the run record and printing an actionable exit message.

### 💾 Persistent Checkpointing
LangGraph state is checkpointed to SQLite after every node, so interrupted runs can theoretically be resumed and the full state history is preserved per thread.

### 📄 Formatted Plan Output
The final plan is printed to the terminal and automatically saved as a timestamped `.txt` file. It includes a visual budget utilisation bar, all selected options, the full itinerary, validation notes, and an LLM usage summary.

### 🖼️ Graph Diagram Export
On startup, the agent graph is rendered as an ASCII diagram in the terminal and exported as a `graph_diagram.png` for visual documentation.

---

## Architecture

```
User Input
    │
    ▼
┌─────────────────────────────────────────────────────────┐
│               Travel Style Classifier                   │
│  (budget / mid-range / luxury / adventure)              │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│                    Orchestrator                         │
│   Routes between agents based on status, retries,       │
│   cost guardrails, and route map                        │
└──┬──────┬──────┬──────┬──────┬──────┬──────┬──────┬────┘
   │      │      │      │      │      │      │      │
   ▼      ▼      ▼      ▼      ▼      ▼      ▼      ▼
Research Budget Flights [CP1] Hotels Itinerary Validate [CP2]
                         ▲                              ▲
                    Human Input                    Human Input
                   (flight choice)          (hotel + plan approval)
                                                        │
                                                        ▼
                                                  Final Plan
                                             (terminal + .txt file)
```

Every agent feeds back into the Orchestrator, which decides the next step based on the `status` field in the shared `TravelPlanState`.

---

## Agent Pipeline

| Step | Agent | What it does |
|------|-------|-------------|
| 1 | **Research** | Fetches destination overview, visa info for Indian passport holders, and 8 practical travel tips |
| 2 | **Budget** | Splits the total INR budget across flights, hotels, food, activities, and a buffer |
| 3 | **Flights** | Generates 3 realistic flight options with timings, prices, pros, and cons |
| — | **Checkpoint 1** | ⏸️ Pauses for human flight selection or rejection |
| 4 | **Hotels** | Generates 3 hotel options at budget/mid/luxury tiers |
| 5 | **Itinerary** | Creates a detailed day-by-day plan incorporating flights, hotel, budget, and travel style |
| 6 | **Validator** | Runs local sanity checks then an LLM deep-review for scheduling and budget conflicts |
| — | **Checkpoint 2** | ⏸️ Pauses for hotel selection and plan approval or change requests |
| 7 | **Final Plan** | Renders the complete formatted plan, saves to file, persists the run record |

---

## Tech Stack

| Category | Technology |
|----------|-----------|
| **Agent orchestration** | [LangGraph](https://github.com/langchain-ai/langgraph) ≥ 0.2.0 |
| **LLM framework** | [LangChain](https://github.com/langchain-ai/langchain) ≥ 0.2.0 |
| **LLM provider** | [Azure OpenAI](https://azure.microsoft.com/en-us/products/ai-services/openai-service) (GPT-4o / GPT-4o-mini) via `langchain-openai` |
| **State persistence** | SQLite via `langgraph-checkpoint-sqlite` |
| **Observability DB** | SQLite (local `data/runs.db`) |
| **Prompt management** | YAML files (`pyyaml`) with auto-version selection |
| **Retry logic** | `tenacity` — exponential backoff on API errors |
| **Graph visualisation** | `matplotlib`, `grandalf` (ASCII + PNG export) |
| **Environment config** | `python-dotenv` |
| **Language** | Python 3.10+ |

---

## Project Structure

```
travel-planner/
│
├── main.py                        # Entry point — CLI, classifier, graph invocation
├── graph.py                       # LangGraph StateGraph definition
├── state.py                       # TravelPlanState TypedDict (all shared fields)
├── requirements.txt
│
├── agents/
│   ├── orchestrator.py            # Routes between agents; enforces cost/retry guards
│   ├── research.py                # Destination info, visa, travel tips
│   ├── budget.py                  # INR budget breakdown
│   ├── flights.py                 # 3 flight options as JSON
│   ├── hotels.py                  # 3 hotel options as JSON
│   ├── itinerary.py               # Day-by-day itinerary (plain text)
│   └── validator.py               # Local checks + LLM deep review
│
├── checkpoints/
│   ├── checkpoint_1.py            # Flight selection logic
│   └── checkpoint_2.py            # Hotel selection + plan approval logic
│
├── utils/
│   ├── llm.py                     # call_llm_safe() with logging + cost tracking
│   ├── prompt_loader.py           # Loads versioned YAML prompts
│   ├── cost_guard.py              # Token caps, USD cost estimation, guardrail checks
│   ├── logger.py                  # SQLite logging for LLM calls and run records
│   ├── failure_classifier.py      # Typed failure classification (6 categories)
│   ├── error_handler.py           # @safe_node decorator for agent exception handling
│   ├── final_plan.py              # Formatted plan renderer + file saver
│   ├── safe_exit.py               # Graceful failure handler with classified exit
│   └── diagram.py                 # ASCII + PNG graph diagram export
│
├── prompts/
│   ├── research/   v1.yaml, v2.yaml
│   ├── budget/     v1.yaml
│   ├── flights/    v1.yaml
│   ├── hotels/     v1.yaml
│   ├── itinerary/  v1.yaml
│   └── validator/  v1.yaml
│
├── classifier/
│   ├── travel_style_classifier.py # Rule-based classifier (budget/mid/luxury/adventure)
│   ├── model_metadata.yaml        # Model version, thresholds, training data reference
│   └── training_data_v1.csv       # Labelled samples for future ML upgrade
│
├── scripts/
│   ├── inspect_run.py             # CLI: print all logs for a run_id
│   └── list_runs.py               # CLI: list all past runs with status + cost
│
└── data/
    └── runs.db                    # Auto-created SQLite database
```

---

## Setup & Installation

### Prerequisites

- Python 3.10 or higher
- An [Azure OpenAI](https://azure.microsoft.com/en-us/products/ai-services/openai-service) resource with a GPT-4o or GPT-4o-mini deployment

### Install

```bash
git clone https://github.com/your-username/travel-planner.git
cd travel-planner

python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
```

For the ASCII graph diagram, also install `grandalf`:

```bash
pip install grandalf
```

---

## Configuration

Create a `.env` file in the project root:

```env
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=gpt-4o-mini
AZURE_OPENAI_API_KEY=your-api-key-here
AZURE_OPENAI_API_VERSION=2024-02-01
```

All four variables are required. The app will fail with a clear error message if any are missing.

---

## Running the Planner

```bash
python main.py
```

You will be prompted for:

1. **Destination** — e.g. `Paris, France`
2. **Origin city** — e.g. `New Delhi, India`
3. **Travel dates** — e.g. `15 June 2025 to 25 June 2025`
4. **Number of travellers** — e.g. `2`
5. **Total budget in INR** — e.g. `200000`

After confirmation, agents run automatically. You will be prompted twice:

- **Checkpoint 1**: Enter `1`, `2`, or `3` to pick a flight, or `reject` to get new options
- **Checkpoint 2**: Enter `approve` to accept the plan, or describe changes (e.g. `more free time on day 3`, `hotel:2`)

The final plan is printed to the terminal and saved as `travel_plan_<destination>_<timestamp>.txt`.

---

## Modules Overview

### Module 1 — Prompt Versioning
System prompts are stored as YAML files in `prompts/<agent>/v*.yaml`. `prompt_loader.py` auto-selects the latest version. To A/B test a new prompt, add `v2.yaml` — no code changes needed. The version used per agent is recorded in `TravelPlanState.prompt_versions_used` and printed in the final plan.

### Module 2 — Observability
`utils/logger.py` writes to two SQLite tables on every run:
- `llm_calls` — one row per LLM invocation with tokens, latency, cost, success/failure
- `run_records` — one summary row per complete run

Inspect with the CLI scripts:
```bash
python scripts/list_runs.py
python scripts/inspect_run.py <run_id>
```

### Module 3 — Cost Guardrails
`utils/cost_guard.py` defines:
- Per-agent hard token caps (overrides YAML `max_tokens` if lower)
- A soft USD cap per run (`$0.10` by default, trivially adjustable)
- A max retry count (`3`)

The orchestrator checks both limits before every routing decision.

### Module 4 — Typed Failure Handling
`utils/failure_classifier.py` inspects the error state and returns one of:
`api_failure` · `prompt_parse_failure` · `validation_conflict` · `human_rejection` · `retry_exhaustion` · `cost_limit_exceeded`

`safe_exit_node` uses this to print an actionable message, persist a typed run record, and show which pipeline steps completed before failure.

### Module 5 — SQLite Persistence
`graph.py` uses `SqliteSaver` (LangGraph's SQLite checkpointer) writing to `data/runs.db`. This gives full LangGraph state history per thread and powers the `logger.py` observability tables in the same file.

### Module 6 — Travel Style Classifier
Before the pipeline starts, `main.py` calls `classify_travel_style()` which computes budget-per-person-per-day and infers destination type from keyword matching, then returns `budget / mid-range / luxury / adventure`. The result is injected into `TravelPlanState.travel_style` and used by the itinerary agent to calibrate activity and restaurant recommendations. Inferences are logged to a `classifier_inferences` table. `classifier/model_metadata.yaml` and `training_data_v1.csv` provide a foundation for upgrading to a trained ML model when enough labelled data is available.

---

## Observability & Logs

All data lands in `data/runs.db` (auto-created). Three tables:

| Table | Contents |
|-------|---------|
| `llm_calls` | Per-call: agent, prompt version, tokens in/out, latency ms, cost USD, success, error |
| `run_records` | Per-run: destination, status, failure type, total tokens, total cost, duration |
| `classifier_inferences` | Per-run: travel style, budget/day, destination type, model version |

```bash
# List all runs
python scripts/list_runs.py

# Deep-dive a specific run
python scripts/inspect_run.py abc12345
```

---

## Cost Guardrails

Default limits in `utils/cost_guard.py` (edit freely):

| Setting | Default |
|---------|---------|
| Max cost per run | $0.10 USD |
| Max retries per run | 3 |
| Research token cap | 800 |
| Budget token cap | 600 |
| Flights token cap | 1,200 |
| Hotels token cap | 1,200 |
| Itinerary token cap | 2,500 |
| Validator token cap | 800 |

A full successful run on GPT-4o-mini typically costs under $0.03 USD.

---

## Prompt Versioning

To update a prompt without touching code:

```bash
# Copy existing prompt
cp prompts/research/v1.yaml prompts/research/v2.yaml

# Edit v2.yaml — change system_message, temperature, or max_tokens
# Update prompt_version: "research-v2"

# Next run automatically picks up v2 (latest version wins)
```

The version used is stored in state and shown in the final plan under **LLM USAGE SUMMARY**.

---

## Travel Style Classifier

| Style | Budget per person/day |
|-------|----------------------|
| Budget | < ₹3,000 |
| Mid-range | ₹3,000 – ₹8,000 |
| Luxury | > ₹8,000 |
| Adventure | ≥ ₹3,000 + adventure destination |

Adventure destinations are detected by keyword (Bali, Nepal, Rishikesh, Ladakh, etc.). The thresholds and destination keywords live in `model_metadata.yaml` and `travel_style_classifier.py` and can be adjusted without touching any agent code.

---
