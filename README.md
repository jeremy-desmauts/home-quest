# home-quest

AI-powered home search agent that automatically finds single-family houses for sale, filters by your criteria, and sends you a daily email digest.

## How it works

```
Discovery Agent  →  finds the right real estate websites for any region (Claude + web_search)
Scraper Agent    →  fetches pages with Playwright, Claude extracts structured listings
Filter Agent     →  price / rooms / property type / distance from target city (geopy)
Storage          →  SQLite deduplication — only new listings trigger emails
Reporter Agent   →  Claude generates a clean HTML email, sent via SMTP
```

## Setup

### 1. Install dependencies

```bash
pip install -e .
playwright install chromium
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env — add your ANTHROPIC_API_KEY and email credentials
```

### 3. Configure search

Edit `config.yaml`:

```yaml
search:
  target_city: "Rennes"
  target_country: "France"
  perimeter_km: 30        # search radius around target city
  price_max: 400000
  min_rooms: 4
```

### 4. Run

```bash
python -m src.main
```

Or with the installed script:

```bash
home-quest
```

## Architecture

| File | Role |
|------|------|
| `src/agents/discovery.py` | Uses Claude + `web_search` tool to find regional real estate portals |
| `src/agents/scraper.py` | Playwright fetches pages, Claude extracts listings as JSON |
| `src/agents/filter_agent.py` | Pure-Python filtering: price, rooms, type, geopy distance |
| `src/agents/reporter.py` | Claude generates HTML email, sent via SMTP |
| `src/storage/db.py` | SQLite store — prevents duplicate alerts |
| `src/tools/` | Page fetcher, geopy wrapper, email sender |

## Gmail setup

In Google Account → Security → App Passwords, generate an app password and use it as `EMAIL_PASSWORD`. Set `SMTP_HOST=smtp.gmail.com` and `SMTP_PORT=587`.
