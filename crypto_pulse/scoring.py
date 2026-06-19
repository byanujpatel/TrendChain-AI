from __future__ import annotations

import math
from collections import Counter
from typing import Iterable

from crypto_pulse.models import ContentItem


PLATFORM_WEIGHTS = {
    "youtube": 1.0,
    "reddit": 1.15,
    "hackernews": 1.05,
    "news": 0.55,
    "coingecko": 0.9,
}

PLATFORM_CAPS = {
    "youtube": 100.0,
    "reddit": 100.0,
    "hackernews": 90.0,
    "coingecko": 75.0,
    "news": 55.0,
}


def calculate_viral_score(item: ContentItem) -> float:
    """Score engagement while rewarding fresh content and meaningful comments."""
    engagement = item.likes + (item.comments * 2) + (item.shares * 3)
    if item.platform == "reddit":
        engagement = item.likes + (item.comments * 3)
    if item.platform == "hackernews":
        engagement = item.likes + (item.comments * 2)
    if item.platform == "coingecko":
        position = int(item.metadata.get("trend_position", 15) or 15)
        return round(max(3.0, 18.0 - position) * PLATFORM_WEIGHTS["coingecko"], 3)
    if item.platform == "news":
        freshness = 72 / max(item.age_hours, 1)
        return round(math.log1p(freshness) * PLATFORM_WEIGHTS["news"], 3)

    velocity = engagement / item.age_hours
    raw_score = (
        math.log1p(max(item.views, 0))
        + math.log1p(max(engagement, 0))
        + math.log1p(max(velocity, 0))
    )
    return round(raw_score * PLATFORM_WEIGHTS.get(item.platform, 0.8), 3)


def score_and_rank(items: Iterable[ContentItem]) -> list[ContentItem]:
    ranked = list(items)
    grouped: dict[str, list[ContentItem]] = {}
    for item in ranked:
        raw_score = calculate_viral_score(item)
        item.metadata["raw_viral_score"] = raw_score
        grouped.setdefault(item.platform, []).append(item)

    for platform, platform_items in grouped.items():
        raw_scores = [float(item.metadata["raw_viral_score"]) for item in platform_items]
        low, high = min(raw_scores), max(raw_scores)
        cap = PLATFORM_CAPS.get(platform, 80.0)
        for item in platform_items:
            raw = float(item.metadata["raw_viral_score"])
            if high == low:
                normalized = cap if raw > 0 else 0.0
            else:
                ratio = (raw - low) / (high - low)
                normalized = cap * (0.2 + (0.8 * ratio))
            item.viral_score = round(normalized, 2)
    return sorted(ranked, key=lambda item: item.viral_score, reverse=True)


def platform_counts(items: Iterable[ContentItem]) -> dict[str, int]:
    return dict(Counter(item.platform for item in items))
