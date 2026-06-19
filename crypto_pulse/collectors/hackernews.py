from __future__ import annotations

from datetime import timedelta

import requests

from crypto_pulse.collectors.base import BaseCollector, CollectorError
from crypto_pulse.models import ContentItem, parse_datetime, utc_now


class HackerNewsCollector(BaseCollector):
    """Search public Hacker News stories through the keyless Algolia HN index."""

    name = "hackernews"
    endpoint = "https://hn.algolia.com/api/v1/search_by_date"

    def __init__(self, timeout: int = 8) -> None:
        self.timeout = timeout

    def collect(self, query: str, days: int, limit: int) -> list[ContentItem]:
        cutoff = int((utc_now() - timedelta(days=days)).timestamp())
        queries = self._queries(query)
        items: list[ContentItem] = []
        failures: list[str] = []

        for search_query in queries:
            try:
                response = requests.get(
                    self.endpoint,
                    params={
                        "query": search_query,
                        "tags": "story",
                        "numericFilters": f"created_at_i>{cutoff}",
                        "hitsPerPage": min(limit, 30),
                    },
                    timeout=self.timeout,
                )
                response.raise_for_status()
            except requests.RequestException as exc:
                failures.append(str(exc))
                continue

            for story in response.json().get("hits", []):
                story_id = story.get("objectID", "")
                discussion_url = f"https://news.ycombinator.com/item?id={story_id}"
                items.append(
                    ContentItem(
                        id=f"hackernews-{story_id}",
                        platform="hackernews",
                        title=story.get("title") or story.get("story_title") or "HN discussion",
                        url=story.get("url") or discussion_url,
                        published_at=parse_datetime(story.get("created_at")),
                        text=(story.get("story_text") or "")[:2500],
                        author=story.get("author", ""),
                        likes=int(story.get("points", 0) or 0),
                        comments=int(story.get("num_comments", 0) or 0),
                        topic=query,
                        metadata={"discussion_url": discussion_url, "matched_query": search_query},
                    )
                )

        unique = {item.id: item for item in items}
        if not unique and failures:
            raise CollectorError(f"Hacker News unavailable: {failures[0]}")
        return sorted(
            unique.values(),
            key=lambda item: item.likes + (item.comments * 2),
            reverse=True,
        )[:limit]

    @staticmethod
    def _queries(query: str) -> list[str]:
        if query.strip().lower() == "crypto":
            return ["cryptocurrency", "bitcoin", "stablecoin blockchain"]
        return [query.strip(), f"{query.strip()} crypto", f"{query.strip()} blockchain"]

