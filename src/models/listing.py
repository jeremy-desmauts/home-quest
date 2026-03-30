from dataclasses import dataclass, field
from datetime import datetime
import hashlib


@dataclass
class Listing:
    url: str
    source_website: str
    title: str = ""
    price: float | None = None
    currency: str | None = None
    address: str | None = None
    city: str | None = None
    rooms: int | None = None
    bedrooms: int | None = None
    area_sqm: float | None = None
    property_type: str | None = None
    description: str | None = None
    images: list[str] = field(default_factory=list)
    distance_km: float | None = None
    scraped_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def id(self) -> str:
        return hashlib.md5(self.url.encode()).hexdigest()
