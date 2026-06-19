from datetime import timedelta

from crypto_pulse.models import ContentItem, utc_now
from crypto_pulse.scoring import calculate_viral_score, score_and_rank


def item(**overrides):
    values = {
        "id": "one",
        "platform": "reddit",
        "title": "Example",
        "url": "https://example.com",
        "published_at": utc_now() - timedelta(hours=4),
        "likes": 100,
        "comments": 20,
    }
    values.update(overrides)
    return ContentItem(**values)


def test_comments_increase_reddit_score():
    quiet = item(comments=0)
    debated = item(id="two", comments=100)
    assert calculate_viral_score(debated) > calculate_viral_score(quiet)


def test_fresher_item_scores_higher_with_same_engagement():
    fresh = item(published_at=utc_now() - timedelta(hours=2))
    old = item(id="two", published_at=utc_now() - timedelta(days=10))
    assert calculate_viral_score(fresh) > calculate_viral_score(old)


def test_score_and_rank_orders_descending():
    low = item(likes=10, comments=1)
    high = item(id="two", likes=1000, comments=200)
    ranked = score_and_rank([low, high])
    assert ranked[0].id == "two"
    assert ranked[0].viral_score >= ranked[1].viral_score

