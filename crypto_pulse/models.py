from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def parse_datetime(value: str | datetime | None) -> datetime:
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if not value:
        return utc_now()
    normalized = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return utc_now()
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


@dataclass
class ContentItem:
    id: str
    platform: str
    title: str
    url: str
    published_at: datetime
    text: str = ""
    author: str = ""
    views: int = 0
    likes: int = 0
    comments: int = 0
    shares: int = 0
    viral_score: float = 0.0
    topic: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def age_hours(self) -> float:
        delta = utc_now() - self.published_at.astimezone(timezone.utc)
        return max(delta.total_seconds() / 3600, 1.0)

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["published_at"] = self.published_at.isoformat()
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ContentItem":
        values = dict(data)
        values["published_at"] = parse_datetime(values.get("published_at"))
        return cls(**values)


@dataclass
class CollectionResult:
    items: list[ContentItem]
    errors: list[str] = field(default_factory=list)
    used_sample_data: bool = False


@dataclass
class AnalysisResult:
    patterns: dict[str, Any]
    ideas: dict[str, list[dict[str, Any]]]
    provider: str
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

