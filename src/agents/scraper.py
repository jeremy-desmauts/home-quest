"""Scraper agent: fetches pages with Playwright, then uses Claude to extract listings."""

import json

from ..llm import MODEL_DEFAULT, get_client
from ..models.listing import Listing
from ..tools.page_fetcher import fetch_page

# Max HTML size passed to Claude (keep cost reasonable)
_MAX_HTML_BYTES = 120_000


def scrape_website(name: str, search_url: str) -> list[Listing]:
    """Scrape one real estate website and return raw Listing objects."""
    print(f"  Scraping {name} …")
    try:
        html = fetch_page(search_url)
        listings = _extract_listings(html, name, search_url)
        print(f"    → {len(listings)} listings extracted")
        return listings
    except Exception as exc:
        print(f"    ✗ Error scraping {name}: {exc}")
        return []


def _extract_listings(html: str, source: str, base_url: str) -> list[Listing]:
    if len(html) > _MAX_HTML_BYTES:
        html = html[:_MAX_HTML_BYTES] + "\n<!-- HTML truncated -->"

    prompt = f"""You are a data extraction expert.

Extract ALL real estate property listings from the HTML below.
For each listing return a JSON object with these fields (use null if unknown):
  title        – property title
  price        – numeric value only (e.g. 320000)
  currency     – ISO code (EUR, USD, GBP …)
  address      – full address string
  city         – city name
  rooms        – total room count (integer)
  bedrooms     – bedroom count (integer)
  area_sqm     – living area in m² (number)
  property_type – "house", "villa", "apartment", etc.
  url          – direct URL to the listing (prepend "{base_url}" if relative)
  description  – one-line summary

Return ONLY a valid JSON array.  If no listings are found, return [].

HTML:
{html}
"""
    response = get_client().messages.create(
        model=MODEL_DEFAULT,
        max_tokens=8192,
        messages=[{"role": "user", "content": prompt}],
    )

    text = next((b.text for b in response.content if b.type == "text"), "")
    text = text.strip()
    start, end = text.find("["), text.rfind("]") + 1
    if start < 0 or end <= start:
        return []

    try:
        raw = json.loads(text[start:end])
    except json.JSONDecodeError:
        return []

    listings = []
    for item in raw:
        url = item.get("url") or ""
        if not url:
            continue
        listings.append(
            Listing(
                url=url,
                source_website=source,
                title=item.get("title") or "",
                price=_to_float(item.get("price")),
                currency=item.get("currency"),
                address=item.get("address"),
                city=item.get("city"),
                rooms=_to_int(item.get("rooms")),
                bedrooms=_to_int(item.get("bedrooms")),
                area_sqm=_to_float(item.get("area_sqm")),
                property_type=item.get("property_type"),
                description=item.get("description"),
            )
        )
    return listings


def _to_float(value) -> float | None:
    try:
        return float(str(value).replace(",", ".").replace(" ", "").replace("\xa0", ""))
    except (TypeError, ValueError):
        return None


def _to_int(value) -> int | None:
    f = _to_float(value)
    return int(f) if f is not None else None
