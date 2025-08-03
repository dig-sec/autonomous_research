"""
Security News Feed Fetcher

Fetches and parses headlines from open security news RSS feeds.
"""
import feedparser
from typing import List, Dict

NEWS_FEEDS = [
    "https://feeds.feedburner.com/TheHackersNews",
    "https://www.bleepingcomputer.com/feed/",
    "https://feeds.feedburner.com/Securityweek"
]

import re
from dateutil import parser as date_parser
from datetime import datetime

def normalize_article(entry: Dict) -> Dict:
    """Normalize article fields and parse date."""
    date_str = entry.get("published", "")
    date = None
    try:
        if date_str:
            date = date_parser.parse(date_str, fuzzy=True)
    except Exception:
        date = None
    title = re.sub(r"\s+", " ", entry.get("title", "")).strip()
    return {
        "id": entry.get("id", entry.get("link", "")),
        "source": entry.get("source", "security_news"),
        "title": title,
        "summary": entry.get("summary", ""),
        "date": date,
        "link": entry.get("link", ""),
        "status": entry.get("status", "pending")
    }

def score_article(article: Dict) -> float:
    """Score article for relevance and authority."""
    score = 0.0
    # Authority: trusted source
    trusted_sources = ["TheHackersNews", "BleepingComputer", "Securityweek"]
    if any(src.lower() in article["link"].lower() for src in trusted_sources):
        score += 0.5
    # Relevance: keywords
    keywords = ["vulnerability", "exploit", "ransomware", "APT", "zero-day", "patch", "breach"]
    text = (article.get("title", "") + " " + article.get("summary", "")).lower()
    score += sum(0.1 for kw in keywords if kw in text)
    # Freshness
    if article.get("date") and isinstance(article["date"], datetime):
        days_old = (datetime.now() - article["date"]).days
        if days_old < 7:
            score += 0.3
        elif days_old < 30:
            score += 0.1
    return round(score, 2)

class SecurityNewsFeed:
    def fetch_news(self, max_items=20) -> List[Dict]:
        news_items = []
        for url in NEWS_FEEDS:
            feed = feedparser.parse(url)
            for entry in feed.entries[:max_items]:
                norm = normalize_article(entry)
                norm["score"] = score_article(norm)
                news_items.append(norm)
        # Sort by score descending
        return sorted(news_items, key=lambda x: x["score"], reverse=True)

# Example usage:
# feed = SecurityNewsFeed()
# news = feed.fetch_news()
# print(news)
