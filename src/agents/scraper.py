"""Scraper agent: fetches pages with Playwright, then uses Claude to extract listings."""

import json
import re

from bs4 import BeautifulSoup

from ..llm import MODEL_DEFAULT, get_client
from ..models.listing import Listing
from ..tools.page_fetcher import fetch_page

# Max characters of cleaned text passed to Claude
_MAX_TEXT_CHARS = 40_000


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


def _clean_html(html: str) -> str:
    """Strip HTML down to readable text to minimise token usage."""
    soup = BeautifulSoup(html, "html.parser")
    # Remove tags that carry no listing data
    for tag in soup(["script", "style", "noscript", "header", "footer", "nav", "svg", "iframe"]):
        tag.decompose()
    text = soup.get_text(separator="\n")
    # Collapse blank lines
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    if len(text) > _MAX_TEXT_CHARS:
        text = text[:_MAX_TEXT_CHARS] + "\n[truncated]"
    return text


def _extract_listings(html: str, source: str, base_url: str) -> list[Listing]:
    text = _clean_html(html)
    print(f"    [scraper] page text: {len(text):,} chars (was {len(html):,} bytes HTML)")

    prompt = f"""You are a data extraction expert.

Extract ALL real estate property listings from the page text below.
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

Page text:
{text}
"""
    response = get_client().models.generate_content(
        model=MODEL_DEFAULT,
        contents=prompt,
    )
    text = response.text.strip()
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
