import os
from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)
from openai import RateLimitError, APITimeoutError, APIConnectionError

load_dotenv()

_llm = None

def get_llm() -> AzureChatOpenAI:
    global _llm
    if _llm is None:
        endpoint   = os.getenv("AZURE_OPENAI_ENDPOINT")
        deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")
        api_key    = os.getenv("AZURE_OPENAI_API_KEY")
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


@retry(
    retry=retry_if_exception_type((RateLimitError, APITimeoutError, APIConnectionError)),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=8),
    reraise=True,
)
def call_llm_safe(system_prompt: str, user_prompt: str) -> str:
    llm = get_llm()
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt),
    ]
    response = llm.invoke(messages)
    return response.content