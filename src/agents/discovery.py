"""Discovery agent: uses Claude + web_search to find real estate sites for any region."""

import json

from ..llm import MODEL_SEARCH, get_client

_TOOLS = [{"type": "web_search_20260209", "name": "web_search"}]


def discover_websites(
    city: str,
    country: str,
    price_max: int = 500_000,
) -> list[dict]:
    """
    Ask Claude (with web search) to find the best real estate listing websites
    for the target region and return ready-to-use search URLs.

    Returns a list of dicts: [{name, search_url, description}, ...]
    """
    prompt = f"""You are a real estate research assistant.

Goal: find the 3-5 most popular websites to search for single-family houses for sale
in or near {city}, {country}, with a budget up to {price_max:,} (local currency).

Use the web search tool to look for real estate listings in {city}.
Based on the results:
1. Identify the top real estate portals that have listings in this area.
2. For each portal, construct the specific **search result URL** that shows
   houses or apartments for sale (not the homepage).

Return ONLY a JSON array — no other text:
[
  {{
    "name": "Website name",
    "search_url": "https://...",
    "description": "Why this site is relevant"
  }}
]
"""
    messages: list[dict] = [{"role": "user", "content": prompt}]
    iteration = 0

    for iteration in range(8):  # max iterations to avoid infinite loops
        print(f"    [discovery] iteration {iteration + 1} — calling Claude …")

        response = get_client().messages.create(
            model=MODEL_SEARCH,
            max_tokens=4096,
            tools=_TOOLS,
            messages=messages,
        )

        _log_response_blocks(response, iteration + 1)

        if response.stop_reason == "end_turn":
            result = _parse_json_array(response)
            print(f"    [discovery] done — {len(result)} site(s) identified")
            return result

        # pause_turn: server-side tool hit iteration cap — re-send to continue
        print(f"    [discovery] stop_reason={response.stop_reason!r} — continuing …")
        messages.append({"role": "assistant", "content": response.content})

    print("    [discovery] reached max iterations without a final answer")
    return []


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _log_response_blocks(response, iteration: int) -> None:
    for block in response.content:
        btype = getattr(block, "type", "unknown")

        if btype == "text":
            preview = block.text.strip().replace("\n", " ")[:120]
            print(f"    [discovery:{iteration}] text: {preview!r}")

        elif btype == "tool_use":
            tool_name = getattr(block, "name", "?")
            tool_input = getattr(block, "input", {})
            if tool_name == "web_search":
                query = tool_input.get("query", "")
                print(f"    [discovery:{iteration}] 🔍 web_search → {query!r}")
            else:
                print(f"    [discovery:{iteration}] tool_use → {tool_name}: {tool_input}")

        elif btype == "web_search_tool_result":
            results = getattr(block, "content", [])
            count = len(results) if isinstance(results, list) else "?"
            print(f"    [discovery:{iteration}] web_search returned {count} result(s):")
            if isinstance(results, list):
                for r in results[:5]:  # show first 5 hits
                    title = r.get("title", "") if isinstance(r, dict) else getattr(r, "title", "")
                    url   = r.get("url", "")   if isinstance(r, dict) else getattr(r, "url", "")
                    print(f"      • {title[:60]}  →  {url}")
                if len(results) > 5:
                    print(f"      … and {len(results) - 5} more")

        else:
            print(f"    [discovery:{iteration}] block type={btype!r}")


def _parse_json_array(response) -> list[dict]:
    for block in response.content:
        if getattr(block, "type", None) == "text":
            text = block.text.strip()
            start, end = text.find("["), text.rfind("]") + 1
            if 0 <= start < end:
                try:
                    data = json.loads(text[start:end])
                    for site in data:
                        print(f"    [discovery] ✓ {site.get('name')} → {site.get('search_url')}")
                    return data
                except json.JSONDecodeError as exc:
                    print(f"    [discovery] ✗ JSON parse error: {exc}")
    print("    [discovery] ✗ no JSON array found in final response")
    return []
