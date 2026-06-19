from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed

from crypto_pulse.collectors import (
    CoinGeckoCollector,
    HackerNewsCollector,
    NewsCollector,
    RedditCollector,
    YouTubeCollector,
)
from crypto_pulse.collectors.base import BaseCollector
from crypto_pulse.config import Settings, get_settings
from crypto_pulse.llm import ClaudeAnalyzer
from crypto_pulse.models import AnalysisResult, CollectionResult, ContentItem
from crypto_pulse.sample_data import load_sample_items
from crypto_pulse.scoring import score_and_rank


class CryptoPulsePipeline:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.collectors: dict[str, BaseCollector] = {
            "reddit": RedditCollector(timeout=self.settings.request_timeout_seconds),
            "youtube": YouTubeCollector(
                api_key=self.settings.youtube_api_key,
                timeout=self.settings.request_timeout_seconds,
            ),
            "hackernews": HackerNewsCollector(timeout=self.settings.request_timeout_seconds),
            "coingecko": CoinGeckoCollector(
                api_key=self.settings.coingecko_demo_api_key,
                timeout=self.settings.request_timeout_seconds,
            ),
            "news": NewsCollector(timeout=self.settings.request_timeout_seconds),
        }
        self.analyzer = ClaudeAnalyzer(
            api_key=self.settings.anthropic_api_key,
            model=self.settings.anthropic_model,
        )

    def collect(
        self,
        query: str,
        days: int,
        sources: list[str],
        mode: str = "live",
    ) -> CollectionResult:
        if mode == "demo":
            return CollectionResult(
                items=score_and_rank(load_sample_items(query)),
                used_sample_data=True,
            )

        errors: list[str] = []
        items: list[ContentItem] = []
        selected = [self.collectors[source] for source in sources if source in self.collectors]

        with ThreadPoolExecutor(max_workers=max(len(selected), 1)) as executor:
            futures = {
                executor.submit(
                    collector.collect,
                    query,
                    days,
                    self.settings.max_items_per_source,
                ): collector.name
                for collector in selected
            }
            for future in as_completed(futures):
                source = futures[future]
                try:
                    items.extend(future.result())
                except Exception as exc:
                    errors.append(f"{source}: {exc}")

        unique = {item.url or item.id: item for item in items}
        ranked = score_and_rank(unique.values())
        return CollectionResult(items=ranked, errors=errors, used_sample_data=False)

    def analyze(self, items: list[ContentItem]) -> AnalysisResult:
        if not items:
            raise ValueError("At least one content item is required for analysis")
        return self.analyzer.analyze_and_generate(items)
