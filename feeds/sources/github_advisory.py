"""
GitHub Security Advisory Feed Fetcher

Fetches and parses recent advisories from the GitHub Security Advisory API.
"""
import requests
from typing import List, Dict

GITHUB_API_URL = "https://api.github.com/security/advisories"

class GitHubAdvisoryFeed:
    def fetch_recent_advisories(self, max_results=20) -> List[Dict]:
        try:
            resp = requests.get(f"{GITHUB_API_URL}?per_page={max_results}", timeout=10)
            resp.raise_for_status()
            data = resp.json()
            return data if isinstance(data, list) else []
        except requests.Timeout:
            print("Timeout while fetching GitHub advisories.")
            return []
        except Exception as e:
            print(f"Error fetching GitHub advisories: {e}")
            return []

    def normalize_advisories(self, advisories: List[Dict]) -> List[Dict]:
        norm = []
        for adv in advisories:
            norm.append({
                "id": adv.get("ghsa_id", adv.get("id", "")),
                "summary": adv.get("summary", ""),
                "description": adv.get("description", ""),
                "severity": adv.get("severity", ""),
                "published": adv.get("published_at", ""),
                "status": "pending",
                "source": "github_advisory"
            })
        return norm

# Example usage:
# feed = GitHubAdvisoryFeed()
# advisories = feed.fetch_recent_advisories()
# normalized = feed.normalize_advisories(advisories)
# print(normalized)
