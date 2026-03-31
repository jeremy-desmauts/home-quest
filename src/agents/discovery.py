"""Discovery agent: uses Gemini + Google Search grounding to find real estate sites."""

import json

from ..llm import MODEL_SEARCH, get_client, get_search_config


def discover_websites(search: dict) -> list[dict]:
    """
    Ask Gemini (with Google Search grounding) to find the best real estate
    listing websites for the target region and return ready-to-use search URLs.

    Returns a list of dicts: [{name, search_url, description}, ...]
    """
    city           = search["target_city"]
    country        = search["target_country"]
    perimeter_km   = search.get("perimeter_km", "")
    price_min      = search.get("price_min", 0)
    price_max      = search.get("price_max", "")
    min_rooms      = search.get("min_rooms", "")
    property_types = search.get("property_types") or []
    types_str      = ", ".join(property_types) if property_types else "any type"

    # Build search queries from the actual property types in config
    queries = [f"{ptype} vendre {city} {country}" for ptype in property_types]
    queries += [f"{ptype} for sale {city} {country}" for ptype in property_types]
    queries_str = "\n".join(f'- "{q}"' for q in queries)

    prompt = f"""You are a real estate research assistant.

Search criteria:
- Location  : {city}, {country}
- Radius    : {perimeter_km} km around {city}
- Budget    : {price_min:,} – {price_max:,} (local currency)
- Min rooms : {min_rooms}
- Property  : {types_str}

## Task

Use Google Search with the following queries to find CURRENTLY ACTIVE listings:
{queries_str}

Identify the 3-5 most popular real estate portals that appeared in the results.

## Rules for the URLs — VERY IMPORTANT

1. ONLY use URLs that actually appeared in the Google Search results — do NOT invent or construct URLs from memory.
2. Use the EXACT URL as returned by Google — do not modify it.
3. Prefer URLs pointing to a **search results page** (multiple listings), not a single property.
4. If you cannot find a valid result URL for a portal, skip it entirely.

## Output

Return ONLY a JSON array — no markdown, no explanation:
[
  {{
    "name": "Website name",
    "search_url": "https://... (exact URL from search results)",
    "description": "Why this site is relevant"
  }}
]
"""

    print(f"    [discovery] calling Gemini with Google Search grounding …")
    response = get_client().models.generate_content(
        model=MODEL_SEARCH,
        contents=prompt,
        config=get_search_config(),
    )
    text = response.text.strip()
    print(f"    [discovery] response received ({len(text)} chars)")

    result = _parse_json_array(text)
    print(f"    [discovery] done — {len(result)} site(s) identified")
    return result


def _parse_json_array(text: str) -> list[dict]:
    start, end = text.find("["), text.rfind("]") + 1
    if 0 <= start < end:
        try:
            data = json.loads(text[start:end])
            for site in data:
                print(f"    [discovery] ✓ {site.get('name')} → {site.get('search_url')}")
            return data
        except json.JSONDecodeError as exc:
            print(f"    [discovery] ✗ JSON parse error: {exc}")
    print("    [discovery] ✗ no JSON array found in response")
    return []
