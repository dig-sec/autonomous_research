#!/usr/bin/env python3
"""
Autonomous Research Runner

Continuously monitors and updates the research queue from all available sources.
This is a simplified autonomous system that works without elasticsearch dependencies.
"""

import time
import sys
import signal
import logging
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from cli.research_manager import ResearchQueueManager

class AutonomousRunner:
    """Simplified autonomous research system."""
    
    def __init__(self, cycle_interval=600):  # 10 minutes default
        self.cycle_interval = cycle_interval
        self.running = True
        self.manager = ResearchQueueManager()
        self.logger = self._setup_logging()
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
    def _setup_logging(self):
        """Setup logging configuration."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('data/logs/autonomous_runner.log'),
                logging.StreamHandler()
            ]
        )
        return logging.getLogger('autonomous_runner')
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        self.logger.info(f"🛑 Received signal {signum}. Shutting down gracefully...")
        self.running = False
    
    def run_cycle(self):
        """Run one collection cycle."""
        cycle_start = datetime.now()
        self.logger.info(f"🔄 Starting collection cycle at {cycle_start.strftime('%Y-%m-%d %H:%M:%S')}")
        
        try:
            # Populate queue from all sources
            queue = self.manager.populate_from_all_sources(force_refresh=True)
            
            # Get and log stats
            stats = self.manager.get_queue_stats()
            total_items = (stats['total_techniques'] + stats['total_cves'] + stats['total_threats'] + 
                          stats['total_news_articles'] + stats['total_threat_intelligence'] + stats['total_advisories'])
            
            cycle_end = datetime.now()
            duration = (cycle_end - cycle_start).total_seconds()
            
            self.logger.info(f"✅ Cycle complete in {duration:.1f}s. Total items: {total_items}")
            self.logger.info(f"   📋 {stats['total_techniques']} techniques, {stats['total_cves']} CVEs")
            self.logger.info(f"   📰 {stats['total_news_articles']} articles, {stats['total_threat_intelligence']} threat intel")
            self.logger.info(f"   🔒 {stats['total_advisories']} advisories")
            
            # Log sources breakdown
            if stats['sources']:
                source_summary = ", ".join([f"{src}: {count}" for src, count in stats['sources'].items()])
                self.logger.info(f"   📡 Sources: {source_summary}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Cycle failed: {e}")
            return False
    
    def run_autonomous(self):
        """Run the autonomous collection loop."""
        self.logger.info(f"🚀 Starting autonomous research runner (cycle interval: {self.cycle_interval}s)")
        self.logger.info(f"📡 Available feed sources: {len(self.manager.feed_integrators)} integrators")
        if self.manager.comprehensive_feeds:
            self.logger.info(f"🔧 Comprehensive feeds enabled")
        
        cycle_count = 0
        
        while self.running:
            try:
                cycle_count += 1
                self.logger.info(f"🔄 Cycle #{cycle_count}")
                
                success = self.run_cycle()
                
                if success:
                    self.logger.info(f"😴 Sleeping for {self.cycle_interval} seconds until next cycle...")
                else:
                    self.logger.warning(f"⚠️  Cycle failed, waiting {self.cycle_interval//2} seconds before retry...")
                    time.sleep(self.cycle_interval // 2)
                    continue
                
                # Sleep in chunks to allow for responsive shutdown
                sleep_chunks = max(1, self.cycle_interval // 10)
                chunk_size = self.cycle_interval / sleep_chunks
                
                for i in range(sleep_chunks):
                    if not self.running:
                        break
                    time.sleep(chunk_size)
                    
            except KeyboardInterrupt:
                self.logger.info("🛑 Interrupted by user")
                break
            except Exception as e:
                self.logger.error(f"❌ Unexpected error: {e}")
                self.logger.info(f"⏱️  Waiting 60 seconds before retry...")
                time.sleep(60)
        
        self.logger.info("🏁 Autonomous runner stopped")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Autonomous Research Runner")
    parser.add_argument("--interval", type=int, default=600,
                       help="Collection cycle interval in seconds (default: 600 = 10 minutes)")
    parser.add_argument("--test", action="store_true",
                       help="Run one test cycle and exit")
    
    args = parser.parse_args()
    
    runner = AutonomousRunner(cycle_interval=args.interval)
    
    if args.test:
        print("🧪 Running test cycle...")
        success = runner.run_cycle()
        print(f"✅ Test cycle {'completed' if success else 'failed'}")
        return 0 if success else 1
    else:
        print(f"🚀 Starting autonomous research runner...")
        print(f"📅 Collection interval: {args.interval} seconds ({args.interval//60} minutes)")
        print("🛑 Press Ctrl+C to stop gracefully")
        runner.run_autonomous()
        return 0


if __name__ == "__main__":
    sys.exit(main())
