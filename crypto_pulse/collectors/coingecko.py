from __future__ import annotations

from hashlib import sha1

import requests

from crypto_pulse.collectors.base import BaseCollector, CollectorError
from crypto_pulse.models import ContentItem, utc_now


class CoinGeckoCollector(BaseCollector):
    name = "coingecko"
    endpoint = "https://api.coingecko.com/api/v3/search/trending"

    def __init__(self, api_key: str = "", timeout: int = 8) -> None:
        self.api_key = api_key
        self.timeout = timeout

    def collect(self, query: str, days: int, limit: int) -> list[ContentItem]:
        headers = {"accept": "application/json"}
        if self.api_key:
            headers["x-cg-demo-api-key"] = self.api_key
        try:
            response = requests.get(self.endpoint, headers=headers, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as exc:
            raise CollectorError(f"CoinGecko unavailable: {exc}") from exc

        items: list[ContentItem] = []
        for position, wrapped in enumerate(data.get("coins", []), 1):
            coin = wrapped.get("item", {})
            name = coin.get("name", "")
            symbol = coin.get("symbol", "")
            coin_id = coin.get("id", "")
            rank = coin.get("market_cap_rank")
            score = coin.get("score", position - 1)
            url = f"https://www.coingecko.com/en/coins/{coin_id}" if coin_id else ""
            items.append(
                ContentItem(
                    id=f"coingecko-coin-{coin_id or position}",
                    platform="coingecko",
                    title=f"Trending coin #{position}: {name} ({symbol})",
                    url=url,
                    published_at=utc_now(),
                    text=f"{name} is currently trending on CoinGecko. Market cap rank: {rank}.",
                    author="CoinGecko",
                    topic=query,
                    metadata={
                        "kind": "coin",
                        "trend_position": position,
                        "coingecko_score": score,
                        "market_cap_rank": rank,
                    },
                )
            )

        for position, category in enumerate(data.get("categories", []), 1):
            name = category.get("name", "")
            category_id = category.get("id") or sha1(name.encode()).hexdigest()[:10]
            items.append(
                ContentItem(
                    id=f"coingecko-category-{category_id}",
                    platform="coingecko",
                    title=f"Trending category #{position}: {name}",
                    url="https://www.coingecko.com/en/categories",
                    published_at=utc_now(),
                    text=(
                        f"{name} is a trending CoinGecko category. "
                        f"24h market change: {category.get('market_cap_1h_change', 0)}."
                    ),
                    author="CoinGecko",
                    topic=query,
                    metadata={
                        "kind": "category",
                        "trend_position": position,
                        "market_cap_change_24h": category.get("market_cap_change_24h"),
                    },
                )
            )

        if not items:
            raise CollectorError("CoinGecko returned no trending assets")
        return items[:limit]

