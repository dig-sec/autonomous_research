"""
AlienVault OTX Feed Fetcher

Fetches and parses recent pulses (threat intelligence reports) from AlienVault OTX.
"""
import requests
from typing import List, Dict

OTX_API_URL = "https://otx.alienvault.com/api/v1/pulses/subscribed"  # Public pulses endpoint

class OTXFeed:
    def fetch_recent_pulses(self, max_results=20) -> List[Dict]:
        try:
            resp = requests.get(f"{OTX_API_URL}?limit={max_results}", timeout=10)
            resp.raise_for_status()
            data = resp.json()
            return data.get("results", [])
        except requests.Timeout:
            print("Timeout while fetching OTX pulses.")
            return []
        except Exception as e:
            print(f"Error fetching OTX pulses: {e}")
            return []

    def normalize_pulses(self, pulses: List[Dict]) -> List[Dict]:
        norm = []
        for pulse in pulses:
            norm.append({
                "id": pulse.get("id", ""),
                "name": pulse.get("name", ""),
                "description": pulse.get("description", ""),
                "created": pulse.get("created", ""),
                "modified": pulse.get("modified", ""),
                "indicators": pulse.get("indicators", []),
                "status": "pending",
                "source": "alienvault_otx"
            })
        return norm

# Example usage:
# feed = OTXFeed()
# pulses = feed.fetch_recent_pulses()
# normalized = feed.normalize_pulses(pulses)
# print(normalized)
