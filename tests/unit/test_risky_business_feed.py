import pytest
from feeds.sources.risky_business_feed import RiskyBusinessFeed

def test_fetch_news_returns_list():
    feed = RiskyBusinessFeed()
    news = feed.fetch_news(max_items=5)
    assert isinstance(news, list)
    assert all(isinstance(item, dict) for item in news)
    # Check required keys
    for item in news:
        for key in ["id", "title", "summary", "published", "link", "status", "source"]:
            assert key in item

def test_populate_queue_adds_new_items():
    feed = RiskyBusinessFeed()
    queue = []
    initial_count = feed.populate_queue(queue, max_items=3)
    assert initial_count > 0
    assert len(queue) == initial_count
    # Running again should not add duplicates
    added_again = feed.populate_queue(queue, max_items=3)
    assert added_again == 0
