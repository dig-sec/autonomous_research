"""
CVE Feed Integration

Fetches recent CVEs and adds them to the research queue.
"""
import json
import sys
from pathlib import Path
import logging

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from feeds.sources.cve_api import CVEFeed

STATUS_PATH = "status.json"
LOG_PATH = "logs/cve_feeds.log"

class CVEFeedIntegrator:
    def __init__(self, status_path=STATUS_PATH, log_path=LOG_PATH):
        self.status_path = Path(status_path)
        self.feed = CVEFeed()
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
        return logging.getLogger("cve_feeds")

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

    def add_cves_to_queue(self, cves):
        status = self.load_status()
        existing_ids = {t["id"] for t in status["techniques"]}
        added = 0
        for cve in cves:
            if cve["id"] and cve["id"] not in existing_ids:
                status["techniques"].append(cve)
                added += 1
        self.save_status(status)
        self.logger.info(f"Added {added} new CVEs to research queue.")

    def run(self):
        try:
            self.logger.info("Fetching recent CVEs...")
            cves = self.feed.fetch_recent_cves()
            normalized = self.feed.normalize_cves(cves)
            self.logger.info(f"Fetched {len(normalized)} CVEs from CVE API.")
            self.add_cves_to_queue(normalized)
        except Exception as e:
            self.logger.error(f"Error during CVE feed integration: {e}")

# Example usage:
# integrator = CVEFeedIntegrator()
# integrator.run()
