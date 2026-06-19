from __future__ import annotations

import json
from pathlib import Path

from crypto_pulse.models import ContentItem


SAMPLE_PATH = Path(__file__).resolve().parent.parent / "data" / "sample_data.json"


def load_sample_items(query: str = "crypto") -> list[ContentItem]:
    with SAMPLE_PATH.open(encoding="utf-8") as file:
        records = json.load(file)
    items = [ContentItem.from_dict(record) for record in records]
    for item in items:
        item.topic = query
    return items

