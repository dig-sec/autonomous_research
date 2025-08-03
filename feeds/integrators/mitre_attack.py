"""
Autonomous Feed Integration

Periodically fetches MITRE ATT&CK techniques and adds them to the research queue.
"""

import json
import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from feeds.sources.mitre_attack_feed import MitreAttackFeed


STATUS_PATH = "status.json"  # Example status file path
LOG_PATH = "logs/autonomous_feeds.log"


class AutonomousFeedIntegrator:
    def __init__(self, status_path=STATUS_PATH, log_path=LOG_PATH):
        self.status_path = Path(status_path)
        self.feed = MitreAttackFeed()
        self.logger = self._setup_logging(log_path)

    def _setup_logging(self, log_path):
        Path(log_path).parent.mkdir(exist_ok=True)
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler(log_path),
                logging.StreamHandler(),
            ],
        )
        return logging.getLogger("autonomous_feeds")


    def load_status(self):
        if self.status_path.exists():
            with open(self.status_path, "r") as f:
                self.logger.info(f"Loaded status from {self.status_path}")
                return json.load(f)
        self.logger.info("No status file found, initializing new queue.")
        return {"techniques": []}


    def save_status(self, status):
        with open(self.status_path, "w") as f:
            json.dump(status, f, indent=2)
        self.logger.info(f"Saved status to {self.status_path}")


    def add_techniques_to_queue(self, techniques):
        status = self.load_status()
        existing_ids = {t["id"] for t in status["techniques"]}
        added = 0
        for tech in techniques:
            if tech["id"] and tech["id"] not in existing_ids:
                status["techniques"].append({
                    "id": tech["id"],
                    "name": tech["name"],
                    "description": tech["description"],
                    "platform": tech["platforms"][0] if tech["platforms"] else "windows",  # Use first platform or default
                    "status": "pending",
                    "source": "mitre_attack"
                })
                added += 1
        self.save_status(status)
        self.logger.info(f"Added {added} new MITRE ATT&CK techniques to research queue.")


    def run(self):
        try:
            self.logger.info("Fetching MITRE ATT&CK techniques...")
            techniques = self.feed.get_latest_techniques()
            normalized = self.feed.normalize_techniques(techniques)
            self.logger.info(f"Fetched {len(normalized)} techniques from MITRE ATT&CK.")
            self.add_techniques_to_queue(normalized)
        except Exception as e:
            self.logger.error(f"Error during feed integration: {e}")

# Example usage:
# integrator = AutonomousFeedIntegrator()
# integrator.run()
