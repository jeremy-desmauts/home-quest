from functools import lru_cache

from geopy.distance import geodesic
from geopy.geocoders import Nominatim

_geolocator = Nominatim(user_agent="home-quest-agent/1.0")


@lru_cache(maxsize=256)
def geocode(place: str) -> tuple[float, float] | None:
    """Return (lat, lon) for a place string, or None if not found."""
    try:
        loc = _geolocator.geocode(place, timeout=10)
        if loc:
            return (loc.latitude, loc.longitude)
    except Exception:
        pass
    return None


def distance_km(city_a: str, city_b: str, country: str = "") -> float | None:
    """Return great-circle distance in km between two city strings."""
    suffix = f", {country}" if country else ""
    coords_a = geocode(f"{city_a}{suffix}")
    coords_b = geocode(f"{city_b}{suffix}")
    if coords_a and coords_b:
        return round(geodesic(coords_a, coords_b).kilometers, 1)
    return None
