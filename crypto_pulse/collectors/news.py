from __future__ import annotations

import calendar
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from hashlib import sha1
from time import mktime

import feedparser
import requests

from crypto_pulse.collectors.base import BaseCollector, CollectorError
from crypto_pulse.models import ContentItem, utc_now


DEFAULT_FEEDS = {
    "Cointelegraph": "https://cointelegraph.com/rss",
    "Decrypt": "https://decrypt.co/feed",
    "Bitcoin Magazine": "https://bitcoinmagazine.com/.rss/full/",
}


class NewsCollector(BaseCollector):
    name = "news"

    def __init__(self, feeds: dict[str, str] | None = None, timeout: int = 15) -> None:
        self.feeds = feeds or DEFAULT_FEEDS
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(
            {"User-Agent": "CryptoPulseAI/0.1 educational-assignment"}
        )

    def collect(self, query: str, days: int, limit: int) -> list[ContentItem]:
        query_terms = {term.lower() for term in query.split() if len(term) > 2}
        items: list[ContentItem] = []
        failed = 0

        with ThreadPoolExecutor(max_workers=min(len(self.feeds), 4)) as executor:
            futures = {
                executor.submit(self._fetch_feed, feed_url): publisher
                for publisher, feed_url in self.feeds.items()
            }
            feeds = []
            for future in as_completed(futures):
                publisher = futures[future]
                try:
                    feeds.append((publisher, future.result()))
                except requests.RequestException:
                    failed += 1

        for publisher, feed in feeds:
            if getattr(feed, "bozo", False) and not feed.entries:
                failed += 1
                continue
            for entry in feed.entries:
                title = entry.get("title", "")
                summary = entry.get("summary", "")
                searchable = f"{title} {summary}".lower()
                if query_terms and query.lower() != "crypto":
                    if not any(term in searchable for term in query_terms):
                        continue
                published = self._published_at(entry)
                if (utc_now() - published).days > days:
                    continue
                link = entry.get("link", "")
                items.append(
                    ContentItem(
                        id=f"news-{sha1(link.encode()).hexdigest()[:12]}",
                        platform="news",
                        title=title,
                        url=link,
                        published_at=published,
                        text=summary[:2500],
                        author=publisher,
                        topic=query,
                        metadata={"publisher": publisher},
                    )
                )

        if not items and failed == len(self.feeds):
            raise CollectorError("All configured news feeds were unavailable")
        return sorted(items, key=lambda item: item.published_at, reverse=True)[:limit]

    def _fetch_feed(self, feed_url: str):
        response = requests.get(
            feed_url,
            timeout=self.timeout,
            headers={"User-Agent": "CryptoPulseAI/0.1 educational-assignment"},
        )
        response.raise_for_status()
        return feedparser.parse(response.content)

    @staticmethod
    def _published_at(entry: dict) -> datetime:
        struct = entry.get("published_parsed") or entry.get("updated_parsed")
        if not struct:
            return utc_now()
        try:
            return datetime.fromtimestamp(calendar.timegm(struct), tz=timezone.utc)
        except (TypeError, ValueError, OverflowError):
            return datetime.fromtimestamp(mktime(struct), tz=timezone.utc)
