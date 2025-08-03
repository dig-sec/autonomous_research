"""
Status Manager

Handles loading and saving project status information.
"""

import json
import os
from pathlib import Path
from typing import Dict
from datetime import datetime


class StatusManager:
    """Manages project status file operations."""

    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.status_file = self.project_root / "project_status.json"

    def load_status(self) -> Dict:
        """Load project status from file."""
        if self.status_file.exists():
            try:
                with open(self.status_file, "r") as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading status: {e}")
        
        return {"techniques": []}

    def save_status(self, status: Dict):
        """Save project status to file."""
        status["last_updated"] = datetime.now().isoformat()
        
        with open(self.status_file, "w") as f:
            json.dump(status, f, indent=2)

    def backup_status(self) -> str:
        """Create a backup of the current status file."""
        if not self.status_file.exists():
            return ""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = self.project_root / f"project_status_backup_{timestamp}.json"
        
        import shutil
        shutil.copy2(self.status_file, backup_file)
        
        return str(backup_file)
