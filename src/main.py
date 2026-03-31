"""HomeQuest — AI-powered home search agent."""

import argparse
from pathlib import Path

import yaml
from dotenv import load_dotenv

from .agents.discovery import discover_websites
from .agents.filter_agent import apply_filters
from .agents.reporter import send_report
from .agents.scraper import scrape_website
from .storage.db import delete_db, filter_new, init_db, save


def _load_config() -> dict:
    with open(Path(__file__).parent.parent / "config.yaml") as f:
        return yaml.safe_load(f)


def main() -> None:
    parser = argparse.ArgumentParser(description="HomeQuest AI home search agent")
    parser.add_argument(
        "--reset-db",
        action="store_true",
        help="Delete the local database before running (re-sends all listings)",
    )
    args = parser.parse_args()

    load_dotenv()

    if args.reset_db:
        print("🗑   Resetting database …")
        delete_db()

    cfg = _load_config()
    search = cfg["search"]

    target_city = search["target_city"]
    target_country = search["target_country"]

    print("\n🏠  HomeQuest starting")
    print(f"    City   : {target_city}, {target_country}")
    print(f"    Radius : {search['perimeter_km']} km")
    print(f"    Budget : up to {search['price_max']:,}")
    print(f"    Rooms  : min {search['min_rooms']}\n")

    init_db()

    # ── 1. Discovery ────────────────────────────────────────────────────────
    print("🔍  Step 1: Discovering real estate websites …")
    websites = discover_websites(search)
    if not websites:
        print("    No websites found. Exiting.")
        return
    print(f"    Found {len(websites)} website(s) to scrape\n")
    for w in websites:
        print(f"    • {w['name']} — {w['search_url']}")

    # ── 2. Scraping ─────────────────────────────────────────────────────────
    print("\n🕷   Step 2: Scraping listings …")
    all_listings = []
    for w in websites:
        all_listings.extend(scrape_website(w["name"], w["search_url"]))
    print(f"\n    Total scraped: {len(all_listings)} listings\n")

    # ── 3. Filtering ────────────────────────────────────────────────────────
    print("🔎  Step 3: Applying filters …")
    filtered = apply_filters(
        listings=all_listings,
        target_city=target_city,
        target_country=target_country,
        price_max=search.get("price_max"),
        price_min=search.get("price_min", 0),
        min_rooms=search.get("min_rooms"),
        perimeter_km=search.get("perimeter_km"),
        property_types=search.get("property_types"),
    )
    print(f"    {len(filtered)} listing(s) match your criteria\n")

    # ── 4. Deduplication ────────────────────────────────────────────────────
    print("🗄   Step 4: Deduplicating against previous runs …")
    new_listings = filter_new(filtered)
    print(f"    {len(new_listings)} new listing(s) since last run\n")

    if new_listings:
        save(new_listings)

        # ── 5. Report ───────────────────────────────────────────────────────
        print("📧  Step 5: Sending email report …")
        send_report(new_listings, target_city, search)

    print("\n✅  HomeQuest run complete!\n")


if __name__ == "__main__":
    main()
