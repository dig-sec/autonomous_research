"""
MITRE ATT&CK Feed Fetcher

Fetches and parses latest techniques/tactics from the MITRE ATT&CK TAXII server.
"""
import requests
import json
from typing import List, Dict

# Updated to use the correct MITRE ATT&CK Enterprise STIX data
MITRE_ATTACK_URL = "https://raw.githubusercontent.com/mitre/cti/master/enterprise-attack/enterprise-attack.json"

class MitreAttackFeed:
    def __init__(self):
        self.data_url = MITRE_ATTACK_URL

    def fetch_collections(self) -> List[Dict]:
        # This method is deprecated - we now fetch directly from GitHub
        return []

    def fetch_objects(self, collection_id: str) -> List[Dict]:
        # This method is deprecated - we now fetch directly from GitHub
        return []

    def get_latest_techniques(self) -> List[Dict]:
        """Get latest techniques from MITRE ATT&CK GitHub repository."""
        try:
            resp = requests.get(self.data_url, timeout=10)  # Faster 10-second timeout
            resp.raise_for_status()
            data = resp.json()
            
            # Extract attack-pattern objects (techniques)
            techniques = []
            for obj in data.get("objects", []):
                if obj.get("type") == "attack-pattern" and not obj.get("revoked", False):
                    techniques.append(obj)
            
            return techniques
        except requests.Timeout:
            print("Timeout while fetching MITRE ATT&CK data.")
            return []
        except Exception as e:
            print(f"Error fetching MITRE ATT&CK data: {e}")
            return []

    def normalize_techniques(self, techniques: List[Dict]) -> List[Dict]:
        # Normalize STIX attack-pattern objects for queueing
        norm = []
        for t in techniques:
            # Extract technique ID from external references
            tech_id = ""
            ext_refs = t.get("external_references", [])
            for ref in ext_refs:
                if ref.get("source_name") == "mitre-attack":
                    tech_id = ref.get("external_id", "")
                    break
            
            # Skip if no valid technique ID
            if not tech_id:
                continue
                
            norm.append({
                "id": tech_id,
                "name": t.get("name", ""),
                "description": t.get("description", ""),
                "platforms": t.get("x_mitre_platforms", []),
                "created": t.get("created", ""),
                "modified": t.get("modified", ""),
                "status": "pending",
                "source": "mitre_attack"
            })
        return norm

# Example usage:
# feed = MitreAttackFeed()
# techniques = feed.get_latest_techniques()
# normalized = feed.normalize_techniques(techniques)
# print(json.dumps(normalized, indent=2))
