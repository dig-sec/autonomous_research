"""
Autonomous Feed Scheduler

Periodically runs all feed integrators to update the research queue.
"""
import time
import logging
from feeds.integrators.mitre_attack import AutonomousFeedIntegrator
from feeds.integrators.cve_integration import CVEFeedIntegrator
# Add imports for other feed integrators as implemented

LOG_PATH = "logs/feed_scheduler.log"

class FeedScheduler:
    def __init__(self, interval_seconds=300, log_path=LOG_PATH):  # 5 minutes for faster feed updates
        self.interval = interval_seconds
        self.logger = self._setup_logging(log_path)
        self.feed_integrators = [
            AutonomousFeedIntegrator(),
            CVEFeedIntegrator(),
            # Add other feed integrators here
        ]

    def _setup_logging(self, log_path):
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler(log_path),
                logging.StreamHandler(),
            ],
        )
        return logging.getLogger("feed_scheduler")

    def run_once(self):
        self.logger.info("Running all feed integrators...")
        for integrator in self.feed_integrators:
            try:
                integrator.run()
            except Exception as e:
                self.logger.error(f"Error running integrator {integrator.__class__.__name__}: {e}")
        self.logger.info("Feed integration cycle complete.")

    def run_forever(self):
        while True:
            self.run_once()
            self.logger.info(f"Sleeping for {self.interval} seconds...")
            time.sleep(self.interval)

# Example usage:
# scheduler = FeedScheduler(interval_seconds=86400)  # Run daily
# scheduler.run_forever()
