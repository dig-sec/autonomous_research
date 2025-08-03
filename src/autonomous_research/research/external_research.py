"""
External Research Module

Conducts research using external sources and APIs.
"""

import os
import requests
import time
from typing import Dict, List, Tuple, Optional
from urllib.parse import quote
import re


class ExternalResearcher:
    """Conducts external research for security techniques."""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "AutonomousResearch/2.0 (Security Research Tool)"
        })
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 1.0  # seconds

    def _rate_limit(self):
        """Enforce rate limiting between requests."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_request_interval:
            time.sleep(self.min_request_interval - time_since_last)
        
        self.last_request_time = time.time()

    def research_technique(self, technique_id: str, platform: str) -> Tuple[str, List[str]]:
        """Research a technique using multiple external sources."""
        
        research_results = []
        sources = []
        
        # Research MITRE ATT&CK directly
        mitre_result = self._research_mitre_attack(technique_id)
        if mitre_result:
            research_results.append(mitre_result)
            sources.append("mitre.org")
        
        # Search for GitHub repositories
        github_results = self._search_github(technique_id, platform)
        if github_results:
            research_results.extend(github_results[:2])  # Limit results
            sources.extend([f"github.com/repo-{i}" for i in range(len(github_results[:2]))])
        
        # Combine results
        if research_results:
            combined_research = "\n\n".join(research_results)
            return combined_research, sources
        
        return "", []

    def _research_mitre_attack(self, technique_id: str) -> Optional[str]:
        """Research technique using MITRE ATT&CK API."""
        try:
            # Use the MITRE ATT&CK STIX data
            url = "https://raw.githubusercontent.com/mitre/cti/master/enterprise-attack/enterprise-attack.json"
            
            self._rate_limit()
            response = self.session.get(url, timeout=60)
            response.raise_for_status()
            
            data = response.json()
            
            # Find the technique
            for obj in data.get("objects", []):
                if obj.get("type") == "attack-pattern":
                    external_refs = obj.get("external_references", [])
                    for ref in external_refs:
                        if ref.get("external_id") == technique_id:
                            name = obj.get("name", "Unknown")
                            description = obj.get("description", "No description available")
                            
                            result = f"MITRE ATT&CK: {technique_id} - {name}\n\n{description}"
                            
                            # Add additional details if available
                            if "x_mitre_platforms" in obj:
                                platforms = ", ".join(obj["x_mitre_platforms"])
                                result += f"\n\nPlatforms: {platforms}"
                            
                            return result
            
            return None
            
        except Exception as e:
            print(f"Error researching MITRE ATT&CK: {e}")
            return None

    def _search_github(self, technique_id: str, platform: str) -> List[str]:
        """Search GitHub for relevant repositories."""
        try:
            # Create search query
            query = f"{technique_id} {platform} security attack technique"
            encoded_query = quote(query)
            
            url = f"https://api.github.com/search/repositories?q={encoded_query}&sort=stars&order=desc"
            
            self._rate_limit()
            response = self.session.get(url, timeout=60)
            
            if response.status_code == 403:  # Rate limited
                print("GitHub API rate limited")
                return []
            
            response.raise_for_status()
            data = response.json()
            
            results = []
            for repo in data.get("items", [])[:3]:  # Limit to top 3
                name = repo.get("name", "")
                description = repo.get("description", "")
                stars = repo.get("stargazers_count", 0)
                url = repo.get("html_url", "")
                
                if description and stars > 5:  # Filter for quality
                    result = f"GitHub Repository: {name} ({stars} stars)\n{description}\nURL: {url}"
                    results.append(result)
            
            return results
            
        except Exception as e:
            print(f"Error searching GitHub: {e}")
            return []

    def search_security_blogs(self, technique_id: str) -> List[str]:
        """Search security blogs for technique information."""
        # Placeholder for blog search functionality
        # Could integrate with RSS feeds, security blog APIs, etc.
        return []

    def get_threat_intelligence(self, technique_id: str) -> Optional[str]:
        """Get threat intelligence for a technique."""
        # Placeholder for threat intelligence integration
        # Could integrate with commercial threat intel APIs
        return None
