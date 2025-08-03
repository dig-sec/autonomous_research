"""
Project Manager

Handles project structure, technique management, and file organization.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime


class ProjectManager:
    """Manages project structure and technique organization."""

    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.techniques_file = self.project_root / "project_status.json"
        
        # Ensure project directories exist
        self._ensure_project_structure()

    def _ensure_project_structure(self):
        """Ensure the project directory structure exists."""
        base_dirs = [
            "output/windows/techniques",
            "output/windows/methods", 
            "output/linux/techniques",
            "output/linux/methods",
            "output/macos/techniques", 
            "output/macos/methods",
            "logs",
            "cache",
            "output",
        ]
        
        for dir_path in base_dirs:
            (self.project_root / dir_path).mkdir(parents=True, exist_ok=True)

    def load_techniques(self) -> List[Dict]:
        """Load all techniques from the project status file."""
        if self.techniques_file.exists():
            try:
                with open(self.techniques_file, "r") as f:
                    data = json.load(f)
                    return data.get("techniques", [])
            except Exception as e:
                print(f"Error loading techniques: {e}")
        return []

    def save_techniques(self, techniques: List[Dict]):
        """Save techniques to the project status file."""
        data = {
            "version": "2.0.0",
            "last_updated": datetime.now().isoformat(),
            "techniques": techniques,
        }
        
        with open(self.techniques_file, "w") as f:
            json.dump(data, f, indent=2)

    def get_technique_directory(self, technique: Dict) -> Path:
        """Get the directory path for a technique."""
        technique_id = technique["id"]
        platform = technique.get("platform", "windows").lower()
        
        if technique_id.startswith(('CD-', 'CO-', 'ET-', 'INF-', 'BTM-', 'IR-', 'TI-')):
            return self.project_root / platform / "methods" / technique_id
        else:
            return self.project_root / platform / "techniques" / technique_id

    def get_techniques_by_platform(self, platform: str) -> List[Dict]:
        """Get all techniques for a specific platform."""
        techniques = self.load_techniques()
        return [t for t in techniques if t.get("platform", "").lower() == platform.lower()]

    def get_techniques_by_status(self, status: str) -> List[Dict]:
        """Get all techniques with a specific status."""
        techniques = self.load_techniques()
        return [t for t in techniques if t.get("status") == status]

    def add_technique(self, technique: Dict) -> bool:
        """Add a new technique to the project."""
        techniques = self.load_techniques()
        
        # Check if technique already exists
        for existing in techniques:
            if existing["id"] == technique["id"]:
                print(f"Technique {technique['id']} already exists")
                return False
        
        # Add new technique
        technique.setdefault("status", "pending")
        technique.setdefault("created_date", datetime.now().isoformat())
        techniques.append(technique)
        
        self.save_techniques(techniques)
        return True

    def update_technique(self, technique_id: str, updates: Dict) -> bool:
        """Update an existing technique."""
        techniques = self.load_techniques()
        
        for technique in techniques:
            if technique["id"] == technique_id:
                technique.update(updates)
                technique["last_updated"] = datetime.now().isoformat()
                self.save_techniques(techniques)
                return True
        
        return False

    def get_project_stats(self) -> Dict:
        """Get project statistics."""
        techniques = self.load_techniques()
        
        stats = {
            "total_techniques": len(techniques),
            "by_platform": {},
            "by_status": {},
            "by_type": {},
        }
        
        for technique in techniques:
            platform = technique.get("platform", "unknown")
            status = technique.get("status", "unknown")
            technique_type = "method" if technique["id"].startswith(('CD-', 'CO-', 'ET-', 'INF-', 'BTM-', 'IR-', 'TI-')) else "mitre"
            
            stats["by_platform"][platform] = stats["by_platform"].get(platform, 0) + 1
            stats["by_status"][status] = stats["by_status"].get(status, 0) + 1
            stats["by_type"][technique_type] = stats["by_type"].get(technique_type, 0) + 1
        
        return stats
