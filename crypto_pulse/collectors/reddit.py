from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from hashlib import sha1

import requests

from crypto_pulse.collectors.base import BaseCollector, CollectorError
from crypto_pulse.models import ContentItem, utc_now


DEFAULT_SUBREDDITS = [
    "CryptoCurrency",
    "Bitcoin",
    "ethereum",
    "solana",
    "CryptoMarkets",
    "defi",
]


class RedditCollector(BaseCollector):
    name = "reddit"

    def __init__(self, timeout: int = 15, subreddits: list[str] | None = None) -> None:
        self.timeout = timeout
        self.subreddits = subreddits or DEFAULT_SUBREDDITS
        self.session = requests.Session()
        self.session.headers.update(
            {"User-Agent": "CryptoPulseAI/0.1 educational-assignment"}
        )

    def collect(self, query: str, days: int, limit: int) -> list[ContentItem]:
        per_subreddit = max(3, min(10, limit // max(len(self.subreddits), 1) + 1))
        items: list[ContentItem] = []
        failures: list[str] = []

        with ThreadPoolExecutor(max_workers=min(len(self.subreddits), 6)) as executor:
            futures = {
                executor.submit(
                    self._collect_subreddit, subreddit, query, days, per_subreddit
                ): subreddit
                for subreddit in self.subreddits
            }
            for future in as_completed(futures):
                subreddit = futures[future]
                try:
                    items.extend(future.result())
                except (requests.RequestException, ValueError, KeyError) as exc:
                    failures.append(f"r/{subreddit}: {exc}")

        unique = {item.url: item for item in items}
        if not unique and failures:
            raise CollectorError("Reddit unavailable: " + "; ".join(failures[:2]))
        return list(unique.values())[:limit]

    def _collect_subreddit(
        self, subreddit: str, query: str, days: int, limit: int
    ) -> list[ContentItem]:
        url = f"https://www.reddit.com/r/{subreddit}/top.json"
        response = self.session.get(
            url,
            params={"t": "month", "limit": min(limit * 2, 25), "raw_json": 1},
            timeout=self.timeout,
        )
        response.raise_for_status()

        cutoff_seconds = days * 86400
        query_terms = {term.lower() for term in query.split() if len(term) > 2}
        results: list[ContentItem] = []
        for child in response.json().get("data", {}).get("children", []):
            post = child.get("data", {})
            published = datetime.fromtimestamp(post.get("created_utc", 0), tz=timezone.utc)
            if (utc_now() - published).total_seconds() > cutoff_seconds:
                continue

            title = post.get("title", "")
            body = post.get("selftext", "")
            searchable = f"{title} {body}".lower()
            if query_terms and query.lower() != "crypto":
                if not any(term in searchable for term in query_terms):
                    continue

            permalink = post.get("permalink", "")
            full_url = f"https://www.reddit.com{permalink}" if permalink else post.get("url", "")
            results.append(
                ContentItem(
                    id=f"reddit-{post.get('id') or sha1(full_url.encode()).hexdigest()[:12]}",
                    platform="reddit",
                    title=title,
                    url=full_url,
                    published_at=published,
                    text=body[:2500],
                    author=post.get("author", ""),
                    likes=int(post.get("score", 0) or 0),
                    comments=int(post.get("num_comments", 0) or 0),
                    topic=query,
                    metadata={"subreddit": subreddit},
                )
            )
        return results[:limit]
