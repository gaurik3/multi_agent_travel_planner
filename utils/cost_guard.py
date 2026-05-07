# Azure OpenAI GPT-4o-mini pricing (as of 2024, update if needed)
# Input:  $0.000150 per 1K tokens
# Output: $0.000600 per 1K tokens
PRICE_INPUT_PER_1K  = 0.000150
PRICE_OUTPUT_PER_1K = 0.000600
INR_PER_USD = 83.0  # Update to current rate

# Maximum total cost allowed per full run (soft cap)
MAX_COST_USD_PER_RUN = 0.10  # ~₹8.30 — very generous for gpt-4o-mini

# Maximum retries allowed across entire run (hard cap)
MAX_RETRIES_PER_RUN = 3

# Per-agent token caps (hard limits passed to Azure OpenAI API)
# These must not exceed the max_tokens in each agent's YAML file.
# If YAML max_tokens is higher than this, this cap wins.
AGENT_TOKEN_CAPS = {
    "research":  800,
    "budget":    600,
    "flights":   1200,
    "hotels":    1200,
    "itinerary": 2500,
    "validator": 800,
}


def get_token_cap(agent_name: str, yaml_max_tokens: int) -> int:
    """
    Returns the effective token cap for an agent.
    Takes the minimum of the YAML-specified value and the hard cap above.
    """
    hard_cap = AGENT_TOKEN_CAPS.get(agent_name, 1000)
    return min(yaml_max_tokens, hard_cap)


def estimate_cost_usd(tokens_in: int, tokens_out: int) -> float:
    """Estimate USD cost for a single LLM call."""
    cost_in  = (tokens_in  / 1000) * PRICE_INPUT_PER_1K
    cost_out = (tokens_out / 1000) * PRICE_OUTPUT_PER_1K
    return round(cost_in + cost_out, 6)


def estimate_cost_inr(tokens_in: int, tokens_out: int) -> float:
    """Estimate INR cost for a single LLM call."""
    return round(estimate_cost_usd(tokens_in, tokens_out) * INR_PER_USD, 4)


def check_run_cost_limit(total_cost_usd_so_far: float) -> bool:
    """
    Returns True if the run is still within cost limits.
    Returns False if the soft cap has been exceeded.
    """
    return total_cost_usd_so_far < MAX_COST_USD_PER_RUN


def check_retry_limit(retry_count: int) -> bool:
    """
    Returns True if retries are still allowed.
    Returns False if max retries exceeded.
    """
    return retry_count < MAX_RETRIES_PER_RUN


def format_cost_summary(total_tokens_in: int, total_tokens_out: int) -> str:
    """Returns a human-readable cost summary for the full run."""
    usd = estimate_cost_usd(total_tokens_in, total_tokens_out)
    inr = estimate_cost_inr(total_tokens_in, total_tokens_out)
    return (
        f"Total tokens used: {total_tokens_in + total_tokens_out} "
        f"(in: {total_tokens_in}, out: {total_tokens_out})\n"
        f"Estimated cost: ${usd:.4f} USD / ₹{inr:.2f} INR"
    )
