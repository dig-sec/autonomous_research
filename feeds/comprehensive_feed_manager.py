#!/usr/bin/env python3
"""
Comprehensive Feed Manager

Integrates all available feed sources into a unified data collection system.
Supports MITRE ATT&CK, CVEs, security news, threat intelligence, and GitHub advisories.
"""

import os
import sys
import json
import time
import logging
from pathlib import Path
from typing import List, Dict, Optional

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import all available feed sources
try:
    from feeds.sources.mitre_attack_feed import MitreAttackFeed
    MITRE_AVAILABLE = True
except ImportError:
    MITRE_AVAILABLE = False

try:
    from feeds.sources.cve_api import CVEFeed
    CVE_AVAILABLE = True
except ImportError:
    CVE_AVAILABLE = False

try:
    from feeds.sources.security_news import SecurityNewsFeed
    NEWS_AVAILABLE = True
except ImportError:
    NEWS_AVAILABLE = False

try:
    from feeds.sources.alien_vault_otx import OTXFeed
    OTX_AVAILABLE = True
except ImportError:
    OTX_AVAILABLE = False

try:
    from feeds.sources.github_advisory import GitHubAdvisoryFeed
    GITHUB_AVAILABLE = True
except ImportError:
    GITHUB_AVAILABLE = False


class ComprehensiveFeedManager:
    """Manages collection from all available feed sources."""
    
    def __init__(self):
        self.logger = self._setup_logging()
        self.data_dir = Path("data/feeds")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize all available feeds
        self.feeds = self._initialize_feeds()
        
    def _setup_logging(self):
        """Setup logging configuration."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        return logging.getLogger('comprehensive_feeds')
    
    def _initialize_feeds(self) -> Dict:
        """Initialize all available feed sources."""
        feeds = {}
        
        if MITRE_AVAILABLE:
            try:
                feeds['mitre_attack'] = MitreAttackFeed()
                self.logger.info("✅ MITRE ATT&CK feed initialized")
            except Exception as e:
                self.logger.warning(f"Could not initialize MITRE feed: {e}")
        
        if CVE_AVAILABLE:
            try:
                feeds['cve'] = CVEFeed()
                self.logger.info("✅ CVE feed initialized")
            except Exception as e:
                self.logger.warning(f"Could not initialize CVE feed: {e}")
        
        if NEWS_AVAILABLE:
            try:
                feeds['security_news'] = SecurityNewsFeed()
                self.logger.info("✅ Security news feed initialized")
            except Exception as e:
                self.logger.warning(f"Could not initialize security news feed: {e}")
        
        if OTX_AVAILABLE:
            try:
                feeds['otx'] = OTXFeed()
                self.logger.info("✅ AlienVault OTX feed initialized")
            except Exception as e:
                self.logger.warning(f"Could not initialize OTX feed: {e}")
        
        if GITHUB_AVAILABLE:
            try:
                feeds['github_advisory'] = GitHubAdvisoryFeed()
                self.logger.info("✅ GitHub advisory feed initialized")
            except Exception as e:
                self.logger.warning(f"Could not initialize GitHub advisory feed: {e}")
        
        self.logger.info(f"📡 Initialized {len(feeds)} feed sources")
        return feeds
    
    def collect_all_data(self, max_items_per_source: int = 20) -> Dict:
        """Collect data from all available sources with deduplication."""
        self.logger.info(f"🔄 Collecting data from {len(self.feeds)} sources...")
        
        all_data = {
            "techniques": [],
            "cves": [],
            "news_articles": [],
            "threat_intelligence": [],
            "advisories": [],
            "metadata": {
                "collection_time": time.time(),
                "sources_queried": list(self.feeds.keys()),
                "max_items_per_source": max_items_per_source
            }
        }
        
        # Load existing data for deduplication
        existing_data = self._load_existing_data()
        
        # Collect MITRE ATT&CK techniques
        if 'mitre_attack' in self.feeds:
            try:
                self.logger.info("📥 Fetching MITRE ATT&CK techniques...")
                techniques = self.feeds['mitre_attack'].get_latest_techniques()
                if hasattr(self.feeds['mitre_attack'], 'normalize_techniques'):
                    techniques = self.feeds['mitre_attack'].normalize_techniques(techniques)
                
                # Deduplicate techniques
                new_techniques = self._deduplicate_items(techniques, existing_data.get("techniques", []))
                all_data["techniques"].extend(new_techniques)
                self.logger.info(f"✅ Added {len(new_techniques)} new MITRE techniques ({len(techniques)} total fetched)")
            except Exception as e:
                self.logger.error(f"❌ Error fetching MITRE data: {e}")
        
        # Collect CVEs
        if 'cve' in self.feeds:
            try:
                self.logger.info("📥 Fetching CVE data...")
                cves = self.feeds['cve'].fetch_recent_cves(max_items_per_source)
                if hasattr(self.feeds['cve'], 'normalize_cves'):
                    cves = self.feeds['cve'].normalize_cves(cves)
                
                # Deduplicate CVEs
                new_cves = self._deduplicate_items(cves, existing_data.get("cves", []))
                all_data["cves"].extend(new_cves)
                self.logger.info(f"✅ Added {len(new_cves)} new CVEs ({len(cves)} total fetched)")
            except Exception as e:
                self.logger.error(f"❌ Error fetching CVE data: {e}")
        
        # Collect Security News
        if 'security_news' in self.feeds:
            try:
                self.logger.info("📥 Fetching security news...")
                news = self.feeds['security_news'].fetch_news(max_items_per_source)
                
                # Deduplicate news articles
                new_news = self._deduplicate_items(news, existing_data.get("news_articles", []))
                all_data["news_articles"].extend(new_news)
                self.logger.info(f"✅ Added {len(new_news)} new news articles ({len(news)} total fetched)")
            except Exception as e:
                self.logger.error(f"❌ Error fetching security news: {e}")
        
        # Collect OTX Threat Intelligence
        if 'otx' in self.feeds:
            try:
                self.logger.info("📥 Fetching OTX threat intelligence...")
                pulses = self.feeds['otx'].fetch_recent_pulses(max_items_per_source)
                if hasattr(self.feeds['otx'], 'normalize_pulses'):
                    pulses = self.feeds['otx'].normalize_pulses(pulses)
                
                # Deduplicate threat intelligence
                new_pulses = self._deduplicate_items(pulses, existing_data.get("threat_intelligence", []))
                all_data["threat_intelligence"].extend(new_pulses)
                self.logger.info(f"✅ Added {len(new_pulses)} new threat intelligence items ({len(pulses)} total fetched)")
            except Exception as e:
                self.logger.error(f"❌ Error fetching OTX data: {e}")
        
        # Collect GitHub Advisories
        if 'github_advisory' in self.feeds:
            try:
                self.logger.info("📥 Fetching GitHub security advisories...")
                advisories = self.feeds['github_advisory'].fetch_recent_advisories(max_items_per_source)
                if hasattr(self.feeds['github_advisory'], 'normalize_advisories'):
                    advisories = self.feeds['github_advisory'].normalize_advisories(advisories)
                
                # Deduplicate advisories
                new_advisories = self._deduplicate_items(advisories, existing_data.get("advisories", []))
                all_data["advisories"].extend(new_advisories)
                self.logger.info(f"✅ Added {len(new_advisories)} new GitHub advisories ({len(advisories)} total fetched)")
            except Exception as e:
                self.logger.error(f"❌ Error fetching GitHub advisory data: {e}")
        
        # Save collected data
        self._save_collected_data(all_data)
        
        # Log summary
        total_items = (len(all_data["techniques"]) + len(all_data["cves"]) + 
                      len(all_data["news_articles"]) + len(all_data["threat_intelligence"]) + 
                      len(all_data["advisories"]))
        
        self.logger.info(f"✅ Collection complete: {total_items} total items from {len(self.feeds)} sources")
        return all_data
    
    def _load_existing_data(self) -> Dict:
        """Load existing data for deduplication checks."""
        latest_file = self.data_dir / "latest_comprehensive_data.json"
        if latest_file.exists():
            try:
                with open(latest_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.warning(f"Could not load existing data for deduplication: {e}")
        return {}
    
    def _deduplicate_items(self, new_items: List[Dict], existing_items: List[Dict]) -> List[Dict]:
        """Remove duplicates based on ID field."""
        if not new_items:
            return []
            
        # Create set of existing IDs for fast lookup
        existing_ids = {item.get("id", "") for item in existing_items if item.get("id")}
        
        # Filter out items that already exist
        deduplicated = []
        duplicates_found = 0
        
        for item in new_items:
            item_id = item.get("id", "")
            if item_id and item_id not in existing_ids:
                deduplicated.append(item)
                existing_ids.add(item_id)  # Add to set to avoid duplicates within new items too
            elif item_id:
                duplicates_found += 1
        
        if duplicates_found > 0:
            self.logger.info(f"🔄 Filtered out {duplicates_found} duplicate items")
            
        return deduplicated
    
    def _save_collected_data(self, data: Dict):
        """Save collected data to files."""
        timestamp = int(time.time())
        
        # Save complete dataset
        output_file = self.data_dir / f"comprehensive_feed_data_{timestamp}.json"
        try:
            with open(output_file, 'w') as f:
                json.dump(data, f, indent=2)
            self.logger.info(f"💾 Saved complete dataset to {output_file}")
        except Exception as e:
            self.logger.error(f"❌ Could not save dataset: {e}")
        
        # Save latest data reference
        latest_file = self.data_dir / "latest_comprehensive_data.json"
        try:
            with open(latest_file, 'w') as f:
                json.dump(data, f, indent=2)
            self.logger.info(f"💾 Updated latest data reference")
        except Exception as e:
            self.logger.error(f"❌ Could not save latest reference: {e}")
    
    def get_feed_status(self) -> Dict:
        """Get status of all feed sources."""
        status = {
            "available_feeds": len(self.feeds),
            "feed_details": {},
            "system_status": {
                "mitre_available": MITRE_AVAILABLE,
                "cve_available": CVE_AVAILABLE,
                "news_available": NEWS_AVAILABLE,
                "otx_available": OTX_AVAILABLE,
                "github_available": GITHUB_AVAILABLE
            }
        }
        
        for feed_name, feed_obj in self.feeds.items():
            status["feed_details"][feed_name] = {
                "type": feed_obj.__class__.__name__,
                "module": feed_obj.__class__.__module__,
                "available": True
            }
        
        return status
    
    def test_all_feeds(self) -> Dict:
        """Test connectivity and functionality of all feeds."""
        test_results = {
            "timestamp": time.time(),
            "total_feeds": len(self.feeds),
            "successful_feeds": 0,
            "failed_feeds": 0,
            "feed_results": {}
        }
        
        for feed_name, feed_obj in self.feeds.items():
            self.logger.info(f"🧪 Testing {feed_name}...")
            
            try:
                # Test with minimal data request
                if hasattr(feed_obj, 'get_latest_techniques'):
                    result = feed_obj.get_latest_techniques()
                    if len(result) > 1:  # Limit to 1 for testing
                        result = result[:1]
                elif hasattr(feed_obj, 'fetch_recent_cves'):
                    result = feed_obj.fetch_recent_cves(1)
                elif hasattr(feed_obj, 'fetch_news'):
                    result = feed_obj.fetch_news(1)
                elif hasattr(feed_obj, 'fetch_recent_pulses'):
                    result = feed_obj.fetch_recent_pulses(1)
                elif hasattr(feed_obj, 'fetch_recent_advisories'):
                    result = feed_obj.fetch_recent_advisories(1)
                else:
                    result = []
                
                test_results["feed_results"][feed_name] = {
                    "status": "success",
                    "items_returned": len(result) if isinstance(result, list) else 0,
                    "error": None
                }
                test_results["successful_feeds"] += 1
                self.logger.info(f"✅ {feed_name} test passed")
                
            except Exception as e:
                test_results["feed_results"][feed_name] = {
                    "status": "failed",
                    "items_returned": 0,
                    "error": str(e)
                }
                test_results["failed_feeds"] += 1
                self.logger.error(f"❌ {feed_name} test failed: {e}")
        
        return test_results


def main():
    """CLI interface for comprehensive feed manager."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Comprehensive Feed Manager")
    parser.add_argument("command", choices=["collect", "status", "test"], 
                       help="Command to execute")
    parser.add_argument("--max-items", type=int, default=20,
                       help="Maximum items per source")
    
    args = parser.parse_args()
    
    # Initialize manager
    manager = ComprehensiveFeedManager()
    
    if args.command == "collect":
        print("🔄 Collecting data from all sources...")
        data = manager.collect_all_data(args.max_items)
        total = (len(data["techniques"]) + len(data["cves"]) + 
                len(data["news_articles"]) + len(data["threat_intelligence"]) + 
                len(data["advisories"]))
        print(f"✅ Collected {total} items total")
        
    elif args.command == "status":
        print("📊 Feed Status:")
        status = manager.get_feed_status()
        print(f"Available feeds: {status['available_feeds']}")
        for feed_name, details in status["feed_details"].items():
            print(f"  {feed_name}: {details['type']}")
        
    elif args.command == "test":
        print("🧪 Testing all feeds...")
        results = manager.test_all_feeds()
        print(f"Total feeds: {results['total_feeds']}")
        print(f"Successful: {results['successful_feeds']}")
        print(f"Failed: {results['failed_feeds']}")
        for feed_name, result in results["feed_results"].items():
            status_icon = "✅" if result["status"] == "success" else "❌"
            print(f"  {status_icon} {feed_name}: {result['status']}")


if __name__ == "__main__":
    main()
