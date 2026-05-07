import os
import time
from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from utils.logger import log_llm_call
from utils.cost_guard import estimate_cost_usd, get_token_cap

load_dotenv()

_llm = None

DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini")


def get_llm() -> AzureChatOpenAI:
    global _llm
    if _llm is None:
        endpoint    = os.getenv("AZURE_OPENAI_ENDPOINT")
        deployment  = os.getenv("AZURE_OPENAI_DEPLOYMENT")
        api_key     = os.getenv("AZURE_OPENAI_API_KEY")
        api_version = os.getenv("AZURE_OPENAI_API_VERSION")

        missing = [
            name for name, val in [
                ("AZURE_OPENAI_ENDPOINT",    endpoint),
                ("AZURE_OPENAI_DEPLOYMENT",  deployment),
                ("AZURE_OPENAI_API_KEY",     api_key),
                ("AZURE_OPENAI_API_VERSION", api_version),
            ] if not val
        ]
        if missing:
            raise EnvironmentError(
                f"Missing required environment variables: {', '.join(missing)}\n"
                "Make sure your .env file contains all four Azure OpenAI variables."
            )

        _llm = AzureChatOpenAI(
            azure_endpoint=endpoint,
            azure_deployment=deployment,
            openai_api_key=api_key,
            openai_api_version=api_version,
            temperature=0.7,
            timeout=60,
        )
        print(f"[LLM] Initialised AzureChatOpenAI — deployment: {deployment}")

    return _llm


def call_llm_safe(
    prompt: str,
    system: str,
    agent_name: str,
    prompt_version: str,
    run_id: str,
    temperature: float = 0.3,
    max_tokens: int = 800,
    current_retry_count: int = 0
) -> dict:
    """
    Makes an LLM call with retry, logging, and cost tracking.

    Returns a dict:
    {
        "content": str,           # the LLM response text
        "tokens_in": int,
        "tokens_out": int,
        "cost_usd": float,
        "success": bool,
        "error": str or None
    }
    """
    llm = get_llm()
    effective_max_tokens = get_token_cap(agent_name, max_tokens)

    last_error = None

    for attempt in range(3):  # max 3 attempts
        start_time = time.time()
        try:
            messages = [
                SystemMessage(content=system),
                HumanMessage(content=prompt),
            ]
            response = llm.invoke(
                messages,
                temperature=temperature,
                max_tokens=effective_max_tokens
            )

            latency_ms = (time.time() - start_time) * 1000

            # Extract token usage — handle both dict and object styles
            usage = getattr(response, "usage_metadata", None) or {}
            if isinstance(usage, dict):
                tokens_in  = usage.get("input_tokens",  0)
                tokens_out = usage.get("output_tokens", 0)
            else:
                tokens_in  = getattr(usage, "input_tokens",  0)
                tokens_out = getattr(usage, "output_tokens", 0)

            cost = estimate_cost_usd(tokens_in, tokens_out)

            log_llm_call(
                run_id=run_id,
                agent_name=agent_name,
                prompt_version=prompt_version,
                deployment_name=DEPLOYMENT_NAME,
                tokens_in=tokens_in,
                tokens_out=tokens_out,
                latency_ms=round(latency_ms, 2),
                retry_count=attempt,
                success=True,
                cost_usd=cost
            )

            return {
                "content":    response.content,
                "tokens_in":  tokens_in,
                "tokens_out": tokens_out,
                "cost_usd":   cost,
                "success":    True,
                "error":      None
            }

        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            last_error = str(e)

            log_llm_call(
                run_id=run_id,
                agent_name=agent_name,
                prompt_version=prompt_version,
                deployment_name=DEPLOYMENT_NAME,
                tokens_in=0,
                tokens_out=0,
                latency_ms=round(latency_ms, 2),
                retry_count=attempt,
                success=False,
                cost_usd=0.0,
                error_message=last_error
            )

            if attempt < 2:
                wait_seconds = 2 ** attempt  # 1s, 2s
                time.sleep(wait_seconds)

    return {
        "content":    "",
        "tokens_in":  0,
        "tokens_out": 0,
        "cost_usd":   0.0,
        "success":    False,
        "error":      last_error
    }
