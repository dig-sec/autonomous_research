"""
CVE Feed Fetcher

Fetches and parses recent vulnerabilities from the CVE API.
"""
import requests
from typing import List, Dict

CVE_API_URL = "https://cveawg.mitre.org/api/cve/"

class CVEFeed:
    def fetch_recent_cves(self, max_results=20) -> List[Dict]:
        try:
            resp = requests.get(f"{CVE_API_URL}?limit={max_results}", timeout=10)
            resp.raise_for_status()
            data = resp.json()
            return data.get("cves", [])
        except requests.Timeout:
            print("Timeout while fetching CVEs.")
            return []
        except Exception as e:
            print(f"Error fetching CVEs: {e}")
            return []

    def normalize_cves(self, cves: List[Dict]) -> List[Dict]:
        norm = []
        for cve in cves:
            cve_id = cve.get("cve_id", "")
            description = cve.get("descriptions", [{}])[0].get("value", "")
            severity = cve.get("metrics", {}).get("cvssMetricV31", [{}])[0].get("cvssData", {}).get("baseSeverity", "")
            published = cve.get("published", "")
            norm.append({
                "id": cve_id,
                "description": description,
                "severity": severity,
                "published": published,
                "status": "pending",
                "source": "cve_api"
            })
        return norm

# Example usage:
# feed = CVEFeed()
# cves = feed.fetch_recent_cves()
# normalized = feed.normalize_cves(cves)
# print(normalized)
