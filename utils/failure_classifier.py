from enum import Enum
from typing import Optional


class FailureType(str, Enum):
    API_FAILURE          = "api_failure"           # Azure OpenAI call failed after retries
    PROMPT_PARSE_FAILURE = "prompt_parse_failure"  # LLM returned invalid JSON / unexpected format
    VALIDATION_CONFLICT  = "validation_conflict"   # Validator found irreconcilable plan errors
    HUMAN_REJECTION      = "human_rejection"       # Human rejected options too many times
    RETRY_EXHAUSTION     = "retry_exhaustion"      # retry_count hit MAX_RETRIES_PER_RUN
    COST_LIMIT_EXCEEDED  = "cost_limit_exceeded"   # total_cost_usd exceeded MAX_COST_USD_PER_RUN
    UNKNOWN              = "unknown"               # catch-all


def classify_failure(state: dict) -> str:
    """
    Inspects state and returns the most specific FailureType string.
    Call this inside safe_exit_node before persisting the run record.
    """
    error_msg   = (state.get("error_message") or "").lower()
    retry_count = state.get("retry_count", 0)
    status      = state.get("status", "")

    if state.get("total_cost_usd", 0.0) >= 0.10:
        return FailureType.COST_LIMIT_EXCEEDED

    if retry_count >= 3:
        # Distinguish why retries were exhausted
        if "human" in error_msg or "rejection" in error_msg:
            return FailureType.HUMAN_REJECTION
        return FailureType.RETRY_EXHAUSTION

    if "json" in error_msg or "parse" in error_msg or "key" in error_msg:
        return FailureType.PROMPT_PARSE_FAILURE

    if "validation" in error_msg or "conflict" in error_msg:
        return FailureType.VALIDATION_CONFLICT

    if "rate" in error_msg or "timeout" in error_msg or "api" in error_msg:
        return FailureType.API_FAILURE

    return FailureType.UNKNOWN


def get_exit_reason(failure_type: str, state: dict) -> str:
    """Returns a human-readable exit reason string."""
    reasons = {
        FailureType.API_FAILURE:
            f"Azure OpenAI API failed after 3 retries. Last error: {state.get('error_message')}",
        FailureType.PROMPT_PARSE_FAILURE:
            f"Agent returned malformed output that could not be parsed.",
        FailureType.VALIDATION_CONFLICT:
            f"Validator found conflicts that could not be resolved: {state.get('validation_notes')}",
        FailureType.HUMAN_REJECTION:
            f"Human rejected options {state.get('retry_count')} times. Max retries reached.",
        FailureType.RETRY_EXHAUSTION:
            f"Maximum retry count ({state.get('retry_count')}) reached.",
        FailureType.COST_LIMIT_EXCEEDED:
            f"Run cost ${state.get('total_cost_usd', 0):.4f} exceeded limit.",
        FailureType.UNKNOWN:
            f"Unexpected failure. Error: {state.get('error_message', 'none')}",
    }
    return reasons.get(failure_type, "Unknown exit reason")
