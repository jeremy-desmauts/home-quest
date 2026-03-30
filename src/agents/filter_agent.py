"""Filter agent: pure-Python filtering of listings by user criteria + geopy distance."""

from ..models.listing import Listing
from ..tools.geo import distance_km


def _matches_property_type(listing: Listing, allowed_types: list[str]) -> bool:
    if not allowed_types:
        return True  # no filter configured — include everything
    if not listing.property_type:
        return True  # unknown type: include by default
    ptype = listing.property_type.lower()
    return any(kw.lower() in ptype for kw in allowed_types)


def apply_filters(
    listings: list[Listing],
    target_city: str,
    target_country: str,
    price_max: float | None = None,
    price_min: float | None = None,
    min_rooms: int | None = None,
    perimeter_km: float | None = None,
    property_types: list[str] | None = None,
) -> list[Listing]:
    """
    Apply all search criteria and annotate each listing with distance_km.
    Returns a price-sorted list of matching listings.
    """
    allowed_types = property_types or []
    kept = []

    for listing in listings:
        label = listing.title or listing.url

        # --- price ---
        if price_max is not None and listing.price and listing.price > price_max:
            print(f"    [filter] ✗ {label!r} — price {listing.price} > max {price_max}")
            continue
        if price_min is not None and listing.price and listing.price < price_min:
            print(f"    [filter] ✗ {label!r} — price {listing.price} < min {price_min}")
            continue

        # --- rooms ---
        if min_rooms is not None and listing.rooms is not None:
            if listing.rooms < min_rooms:
                print(f"    [filter] ✗ {label!r} — rooms {listing.rooms} < min {min_rooms}")
                continue

        # --- property type ---
        if not _matches_property_type(listing, allowed_types):
            print(f"    [filter] ✗ {label!r} — type {listing.property_type!r} not in {allowed_types}")
            continue

        # --- distance / perimeter ---
        if perimeter_km is not None and listing.city:
            dist = distance_km(listing.city, target_city, target_country)
            if dist is not None:
                if dist > perimeter_km:
                    print(f"    [filter] ✗ {label!r} — {listing.city} is {dist} km away (max {perimeter_km})")
                    continue
                listing.distance_km = dist
            # If geocoding fails, include the listing (better to over-include)

        print(f"    [filter] ✓ {label!r}")
        kept.append(listing)

    # Sort by price ascending (unknown price goes last)
    kept.sort(key=lambda l: l.price if l.price is not None else float("inf"))
    return kept
