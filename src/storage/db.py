import sqlite3
from contextlib import contextmanager
from pathlib import Path

from ..models.listing import Listing

DB_PATH = Path("home_quest.db")


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def delete_db() -> None:
    """Delete the database file (resets all seen listings)."""
    if DB_PATH.exists():
        DB_PATH.unlink()
        print(f"    Database deleted: {DB_PATH}")
    else:
        print(f"    No database found at {DB_PATH} — nothing to delete.")


def init_db():
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS listings (
                id          TEXT PRIMARY KEY,
                url         TEXT NOT NULL,
                source      TEXT,
                title       TEXT,
                price       REAL,
                currency    TEXT,
                address     TEXT,
                city        TEXT,
                rooms       INTEGER,
                area_sqm    REAL,
                prop_type   TEXT,
                distance_km REAL,
                scraped_at  TEXT
            )
        """)


def filter_new(listings: list[Listing]) -> list[Listing]:
    """Return only listings not already stored."""
    with get_conn() as conn:
        new = []
        for listing in listings:
            exists = conn.execute(
                "SELECT 1 FROM listings WHERE id = ?", (listing.id,)
            ).fetchone()
            if not exists:
                new.append(listing)
        return new


def save(listings: list[Listing]):
    with get_conn() as conn:
        conn.executemany(
            """
            INSERT OR IGNORE INTO listings
            (id, url, source, title, price, currency, address, city,
             rooms, area_sqm, prop_type, distance_km, scraped_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            [
                (
                    l.id, l.url, l.source_website, l.title,
                    l.price, l.currency, l.address, l.city,
                    l.rooms, l.area_sqm, l.property_type,
                    l.distance_km, l.scraped_at.isoformat(),
                )
                for l in listings
            ],
        )
