from __future__ import annotations

from datetime import timedelta

import requests

from crypto_pulse.collectors.base import BaseCollector, CollectorError
from crypto_pulse.models import ContentItem, parse_datetime, utc_now


class YouTubeCollector(BaseCollector):
    name = "youtube"
    base_url = "https://www.googleapis.com/youtube/v3"

    def __init__(self, api_key: str, timeout: int = 15) -> None:
        self.api_key = api_key
        self.timeout = timeout

    def collect(self, query: str, days: int, limit: int) -> list[ContentItem]:
        if not self.api_key:
            raise CollectorError("YOUTUBE_API_KEY is not configured")

        published_after = (utc_now() - timedelta(days=days)).isoformat().replace("+00:00", "Z")
        search_query = self._search_query(query)
        try:
            search_response = requests.get(
                f"{self.base_url}/search",
                params={
                    "part": "snippet",
                    "type": "video",
                    "q": search_query,
                    "order": "relevance",
                    "videoDuration": "medium",
                    "publishedAfter": published_after,
                    "maxResults": min(limit, 50),
                    "key": self.api_key,
                },
                timeout=self.timeout,
            )
            search_response.raise_for_status()
            search_items = search_response.json().get("items", [])
            video_ids = [
                item.get("id", {}).get("videoId")
                for item in search_items
                if item.get("id", {}).get("videoId")
            ]
            if not video_ids:
                return []

            stats_response = requests.get(
                f"{self.base_url}/videos",
                params={
                    "part": "statistics,snippet",
                    "id": ",".join(video_ids),
                    "key": self.api_key,
                },
                timeout=self.timeout,
            )
            stats_response.raise_for_status()
        except requests.RequestException as exc:
            raise CollectorError(f"YouTube unavailable: {exc}") from exc

        results: list[ContentItem] = []
        query_terms = {term.lower() for term in query.split() if len(term) > 2}
        for video in stats_response.json().get("items", []):
            snippet = video.get("snippet", {})
            stats = video.get("statistics", {})
            video_id = video.get("id", "")
            title = snippet.get("title", "")
            description = snippet.get("description", "")
            searchable = f"{title} {description}".lower()
            if query.strip().lower() != "crypto" and query_terms:
                if not any(term in searchable for term in query_terms):
                    continue
            results.append(
                ContentItem(
                    id=f"youtube-{video_id}",
                    platform="youtube",
                    title=title,
                    url=f"https://www.youtube.com/watch?v={video_id}",
                    published_at=parse_datetime(snippet.get("publishedAt")),
                    text=description[:2500],
                    author=snippet.get("channelTitle", ""),
                    views=int(stats.get("viewCount", 0) or 0),
                    likes=int(stats.get("likeCount", 0) or 0),
                    comments=int(stats.get("commentCount", 0) or 0),
                    topic=query,
                    metadata={"channel_id": snippet.get("channelId", "")},
                )
            )
        return results

    @staticmethod
    def _search_query(query: str) -> str:
        topic = query.strip()
        if topic.lower() == "crypto":
            return "crypto news analysis explained -shorts -dropshipping"
        return f"{topic} crypto news analysis explained -shorts"
