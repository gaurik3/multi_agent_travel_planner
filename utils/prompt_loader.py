import yaml
import os
from typing import Optional

PROMPTS_DIR = os.path.join(os.path.dirname(__file__), "..", "prompts")


def load_prompt(agent_name: str, version: Optional[str] = None) -> dict:
    """
    Load a prompt YAML for a given agent.
    If version is None, loads the highest available version.

    Returns a dict with keys:
      prompt_version, temperature, max_tokens, system_message
    """
    agent_dir = os.path.join(PROMPTS_DIR, agent_name)

    if not os.path.exists(agent_dir):
        raise FileNotFoundError(f"No prompt directory found for agent: {agent_name}")

    if version:
        filepath = os.path.join(agent_dir, f"{version}.yaml")
    else:
        # Auto-select latest version
        versions = sorted([
            f for f in os.listdir(agent_dir) if f.endswith(".yaml")
        ])
        if not versions:
            raise FileNotFoundError(f"No YAML prompt files found in {agent_dir}")
        filepath = os.path.join(agent_dir, versions[-1])

    with open(filepath, "r") as f:
        prompt_data = yaml.safe_load(f)

    required_keys = ["prompt_version", "temperature", "max_tokens", "system_message"]
    for key in required_keys:
        if key not in prompt_data:
            raise ValueError(f"Prompt file {filepath} is missing required key: {key}")

    return prompt_data


def get_active_version(agent_name: str) -> str:
    """Returns the version string of the latest prompt for an agent."""
    prompt = load_prompt(agent_name)
    return prompt["prompt_version"]
