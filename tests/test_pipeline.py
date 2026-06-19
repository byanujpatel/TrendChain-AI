from crypto_pulse.config import Settings
from crypto_pulse.models import ContentItem, utc_now
from crypto_pulse.pipeline import CryptoPulsePipeline
from crypto_pulse.sample_data import load_sample_items
from crypto_pulse.scoring import score_and_rank


def test_offline_analysis_returns_all_required_ideas():
    settings = Settings(anthropic_api_key="", youtube_api_key="")
    pipeline = CryptoPulsePipeline(settings)
    result = pipeline.analyze(score_and_rank(load_sample_items()))
    assert len(result.ideas["instagram_reels"]) == 5
    assert len(result.ideas["youtube_videos"]) == 3
    assert len(result.ideas["twitter_threads"]) == 3
    assert result.provider == "local fallback"


def test_demo_collection_is_explicitly_labelled():
    pipeline = CryptoPulsePipeline(Settings())
    result = pipeline.collect("crypto", 30, [], mode="demo")
    assert result.used_sample_data is True
    assert len(result.items) > 0


def test_sample_data_contains_multiple_platforms_and_engagement():
    items = score_and_rank(load_sample_items())
    assert len({item.platform for item in items}) >= 3
    assert items[0].viral_score > 0


def test_content_item_smoke_fixture():
    item = ContentItem(
        id="fixture",
        platform="news",
        title="Fixture",
        url="https://example.com",
        published_at=utc_now(),
    )
    assert item.platform == "news"
