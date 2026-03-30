"""Shared LLM client and model configuration."""

import os

import anthropic

# Change these to switch models across the entire app
MODEL_DEFAULT = "claude-sonnet-4-6"
MODEL_SEARCH  = "claude-sonnet-4-6"  # must support web_search tool


def get_client() -> anthropic.Anthropic:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError(
            "ANTHROPIC_API_KEY is not set. "
            "Make sure your .env file exists and load_dotenv() has been called."
        )
    return anthropic.Anthropic(api_key=api_key)
