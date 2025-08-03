"""
Risky Business Feed Fetcher

Fetches and parses headlines from Risky Business RSS feeds.
"""
import feedparser
from typing import List, Dict

RISKY_BUSINESS_FEEDS = [
    "https://risky.biz/feeds/risky-business",
    "https://risky.biz/feeds/risky-business-news",
    "https://risky.biz/rss.xml"
]


class RiskyBusinessFeed:
    def fetch_news(self, max_items=20) -> List[Dict]:
        news_items = []
        for url in RISKY_BUSINESS_FEEDS:
            feed = feedparser.parse(url)
            for entry in feed.entries[:max_items]:
                news_items.append({
                    "id": entry.get("id", entry.get("link", "")),
                    "title": entry.get("title", ""),
                    "summary": entry.get("summary", ""),
                    "published": entry.get("published", ""),
                    "link": entry.get("link", ""),
                    "status": "pending",
                    "source": "risky_business"
                })
        return news_items

    def populate_queue(self, queue: List[Dict], max_items=20) -> int:
        """Fetch latest news and populate the provided queue with pending items."""
        news_items = self.fetch_news(max_items=max_items)
        initial_len = len(queue)
        for item in news_items:
            if item["id"] not in {q["id"] for q in queue}:
                queue.append(item)
        return len(queue) - initial_len

# Example usage:
# feed = RiskyBusinessFeed()
# news = feed.fetch_news()
# print(news)
