"""Shared LLM client and model configuration — Google Gemini."""

import os

from google import genai
from google.genai import types

# Change these to switch models across the entire app
MODEL_DEFAULT = "gemini-2.5-flash"
MODEL_SEARCH  = "gemini-2.5-flash"  # supports Google Search grounding


_client: genai.Client | None = None


def get_client() -> genai.Client:
    global _client
    if _client is None:
        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise RuntimeError(
                "GOOGLE_API_KEY is not set. "
                "Make sure your .env file exists and load_dotenv() has been called."
            )
        _client = genai.Client(api_key=api_key)
    return _client


def get_search_config() -> types.GenerateContentConfig:
    """Config that enables Google Search grounding (for discovery agent)."""
    return types.GenerateContentConfig(
        tools=[types.Tool(google_search=types.GoogleSearch())]
    )
