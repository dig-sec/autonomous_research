#!/usr/bin/env python3
"""
Research Manager - Main CLI Interface

Centralized management interface for the autonomous research system.
Provides queue population, knowledge base building, and system monitoring.
"""
import os
import sys
import argparse
import logging
import time
from pathlib import Path
from typing import List, Dict, Optional
import json

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

# Setup logging early
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import with fallbacks for missing modules
try:
    from src.autonomous_research.config.secure_config import load_config, get_elasticsearch_config
    from src.autonomous_research.core.autonomous_system import AutonomousResearchSystem
    from src.autonomous_research.rag.integration import StandaloneElasticsearchRAG
    from src.autonomous_research.core.elasticsearch_queue_manager import ElasticsearchQueueManager
    CONFIG_AVAILABLE = True
    
    # Import custom techniques manager
    try:
        from src.autonomous_research.knowledge.custom_techniques import (
            CustomTechniqueManager, CustomTechnique, ProceduralCluster
        )
        custom_tech_available = True
    except ImportError:
        custom_tech_available = False
        logger.warning("Custom techniques module not available")

except ImportError as e:
    logger.error(f"Failed to import required modules: {e}")
    sys.exit(1)

try:
    from feeds.comprehensive_feed_manager import ComprehensiveFeedManager
    from feeds.integrators.mitre_attack import AutonomousFeedIntegrator
    from feeds.integrators.cve_integration import CVEFeedIntegrator
    FEEDS_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Missing feed modules: {e}")
    FEEDS_AVAILABLE = False


class ResearchQueueManager:
    """Manages the central research queue and knowledge base building using Elasticsearch."""
    
    def __init__(self):
        # Ensure data directories exist for legacy support
        Path("data/queue").mkdir(parents=True, exist_ok=True)
        Path("data/logs").mkdir(parents=True, exist_ok=True)
        
        # Legacy file paths for migration
        self.queue_file = "data/queue/research_queue.json"
        self.status_file = "data/queue/project_status.json"
        self.logger = self._setup_logging()
        
        # Initialize Elasticsearch queue manager
        if CONFIG_AVAILABLE:
            try:
                self.es_queue = ElasticsearchQueueManager()
                self.logger.info("✅ Elasticsearch queue manager initialized")
            except Exception as e:
                self.logger.error(f"❌ Could not initialize Elasticsearch queue: {e}")
                self.es_queue = None
        else:
            self.es_queue = None
        
        # Initialize configuration if available
        if CONFIG_AVAILABLE:
            try:
                self.config = load_config()
            except Exception as e:
                self.logger.warning(f"Could not load config: {e}")
                self.config = {}
        else:
            self.config = {}
        
        # Initialize components
        self.feed_integrators = self._initialize_feeds()
        self.comprehensive_feeds = self._initialize_comprehensive_feeds()
        self.autonomous_system = None
        self.rag_system = None
        
    def _setup_logging(self):
        """Setup logging configuration."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('data/logs/research_queue.log'),
                logging.StreamHandler()
            ]
        )
        return logging.getLogger('research_queue')
    
    def _initialize_feeds(self) -> List:
        """Initialize all feed integrators."""
        feeds = []
        if FEEDS_AVAILABLE:
            try:
                feeds.extend([
                    AutonomousFeedIntegrator(),
                    CVEFeedIntegrator(),
                ])
            except Exception as e:
                self.logger.warning(f"Could not initialize feeds: {e}")
        return feeds
    
    def _initialize_comprehensive_feeds(self):
        """Initialize comprehensive feed manager."""
        if FEEDS_AVAILABLE:
            try:
                return ComprehensiveFeedManager()
            except Exception as e:
                self.logger.warning(f"Could not initialize comprehensive feeds: {e}")
        return None
    
    def load_queue(self) -> Dict:
        """Load current research queue."""
        if Path(self.queue_file).exists():
            try:
                with open(self.queue_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.error(f"Could not load queue: {e}")
        return {"techniques": [], "cves": [], "threats": [], "metadata": {}}
    
    def save_queue(self, queue: Dict):
        """Save research queue to file."""
        try:
            with open(self.queue_file, 'w') as f:
                json.dump(queue, f, indent=2)
            self.logger.info(f"Saved queue with {len(queue.get('techniques', []))} techniques, "
                            f"{len(queue.get('cves', []))} CVEs")
        except Exception as e:
            self.logger.error(f"Could not save queue: {e}")
    
    def populate_from_all_sources(self, force_refresh: bool = False):
        """Populate queue from all available sources using Elasticsearch."""
        self.logger.info("🔄 Populating research queue from all sources...")
        
        # Use Elasticsearch queue if available
        if self.es_queue:
            return self._populate_elasticsearch_queue(force_refresh)
        else:
            # Fallback to legacy file-based queue
            return self._populate_legacy_queue(force_refresh)
    
    def _populate_elasticsearch_queue(self, force_refresh: bool = False):
        """Populate Elasticsearch-based queue."""
        if not self.es_queue:
            self.logger.error("Elasticsearch queue not available")
            return {}
        
        initial_stats = self.es_queue.get_queue_stats()
        initial_total = initial_stats.get("total_items", 0)
        
        # Use comprehensive feed manager if available
        if self.comprehensive_feeds:
            try:
                self.logger.info("📡 Using comprehensive feed collection...")
                comprehensive_data = self.comprehensive_feeds.collect_all_data(max_items_per_source=50)
                
                # Add different types of data to queue
                added_counts = {}
                for data_type, items in comprehensive_data.items():
                    if items:
                        count = self.es_queue.add_to_queue(
                            items, item_type=data_type, 
                            source="comprehensive_feeds"
                        )
                        added_counts[data_type] = count
                
                self.logger.info("✅ Comprehensive feed collection complete")
                self.logger.info(f"   Added: {added_counts}")
                
            except Exception as e:
                self.logger.error(f"❌ Error with comprehensive feeds: {e}")
        
        # Run legacy feed integrators (skip for now - can be added later)
        # legacy_data = self._collect_legacy_feed_data()
        # if legacy_data:
        #     for data_type, items in legacy_data.items():
        #         if items:
        #             self.es_queue.add_to_queue(
        #                 items, item_type=data_type,
        #                 source="legacy_feeds"
        #             )
        
        # Get final stats
        final_stats = self.es_queue.get_queue_stats()
        final_total = final_stats.get("total_items", 0)
        
        self.logger.info(f"✅ Queue population complete: {final_total - initial_total} new items added")
        self.logger.info(f"   Total items in queue: {final_total}")
        
        # Update system status
        self.es_queue.update_system_status(
            "queue_manager", "populated", 
            statistics=final_stats
        )
        
        return final_stats
    
    def _populate_legacy_queue(self, force_refresh: bool = False):
        """Legacy file-based queue population."""
        self.logger.info("Using legacy file-based queue...")
        
        queue = self.load_queue()
        initial_techniques = len(queue.get("techniques", []))
        initial_cves = len(queue.get("cves", []))
        
        # Use comprehensive feed manager if available
        if self.comprehensive_feeds:
            try:
                self.logger.info("📡 Using comprehensive feed collection...")
                comprehensive_data = self.comprehensive_feeds.collect_all_data(max_items_per_source=50)
                
                # Merge comprehensive data into queue
                queue.setdefault("techniques", []).extend(comprehensive_data.get("techniques", []))
                queue.setdefault("cves", []).extend(comprehensive_data.get("cves", []))
                queue.setdefault("news_articles", []).extend(comprehensive_data.get("news_articles", []))
                queue.setdefault("threat_intelligence", []).extend(comprehensive_data.get("threat_intelligence", []))
                queue.setdefault("advisories", []).extend(comprehensive_data.get("advisories", []))
                
                self.logger.info("✅ Comprehensive feed collection complete")
                
            except Exception as e:
                self.logger.error(f"❌ Error with comprehensive feeds: {e}")
                self.logger.info("🔄 Falling back to legacy feed integrators...")
        
        # Run legacy feed integrators as backup or primary
        for integrator in self.feed_integrators:
            try:
                self.logger.info(f"Running {integrator.__class__.__name__}...")
                integrator.run()
            except Exception as e:
                self.logger.error(f"Error running {integrator.__class__.__name__}: {e}")
        
        # Consolidate data from feeds
        self._consolidate_feed_data(queue)
        
        # Deduplicate the entire queue
        queue = self._deduplicate_queue(queue)
        
        # Save consolidated queue
        self.save_queue(queue)
        
        final_techniques = len(queue.get("techniques", []))
        final_cves = len(queue.get("cves", []))
        final_news = len(queue.get("news_articles", []))
        final_threats = len(queue.get("threat_intelligence", []))
        final_advisories = len(queue.get("advisories", []))
        
        self.logger.info(f"✅ Queue population complete: "
                        f"{final_techniques - initial_techniques} new techniques, "
                        f"{final_cves - initial_cves} new CVEs, "
                        f"{final_news} news articles, "
                        f"{final_threats} threat intel, "
                        f"{final_advisories} advisories added")
        return queue
    
    def _consolidate_feed_data(self, queue: Dict):
        """Consolidate data from individual feed status files."""
        # Check both old and new status file locations
        status_files = [
            "data/queue/project_status.json",
            "data/queue/status.json", 
            "project_status.json",  # Legacy location
            "status.json"           # Legacy location
        ]
        
        for status_file in status_files:
            if Path(status_file).exists():
                try:
                    with open(status_file, 'r') as f:
                        status_data = json.load(f)
                    
                    # Add new techniques that aren't already in queue
                    existing_ids = {t.get("id") for t in queue.get("techniques", [])}
                    for technique in status_data.get("techniques", []):
                        if technique.get("id") not in existing_ids:
                            queue.setdefault("techniques", []).append(technique)
                            
                except Exception as e:
                    self.logger.warning(f"Could not load {status_file}: {e}")
        
        # Update metadata
        queue.setdefault("metadata", {})["last_updated"] = time.time()
    
    def _deduplicate_queue(self, queue: Dict) -> Dict:
        """Remove duplicates from the entire queue."""
        self.logger.info("🔄 Deduplicating queue items...")
        
        # Track original counts
        original_counts = {
            "techniques": len(queue.get("techniques", [])),
            "cves": len(queue.get("cves", [])),
            "news_articles": len(queue.get("news_articles", [])),
            "threat_intelligence": len(queue.get("threat_intelligence", [])),
            "advisories": len(queue.get("advisories", []))
        }
        
        # Deduplicate each category
        for category in ["techniques", "cves", "news_articles", "threat_intelligence", "advisories"]:
            items = queue.get(category, [])
            if items:
                deduplicated = self._deduplicate_items_by_id(items)
                queue[category] = deduplicated
                
                removed = len(items) - len(deduplicated)
                if removed > 0:
                    self.logger.info(f"   📋 Removed {removed} duplicate {category}")
        
        # Log summary
        new_counts = {
            "techniques": len(queue.get("techniques", [])),
            "cves": len(queue.get("cves", [])),
            "news_articles": len(queue.get("news_articles", [])),
            "threat_intelligence": len(queue.get("threat_intelligence", [])),
            "advisories": len(queue.get("advisories", []))
        }
        
        total_removed = sum(original_counts[k] - new_counts[k] for k in original_counts.keys())
        if total_removed > 0:
            self.logger.info(f"✅ Deduplication complete: removed {total_removed} duplicate items")
        
        return queue
    
    def _deduplicate_items_by_id(self, items: List[Dict]) -> List[Dict]:
        """Remove duplicates from a list of items based on ID."""
        seen_ids = set()
        deduplicated = []
        
        for item in items:
            item_id = item.get("id", "")
            if item_id and item_id not in seen_ids:
                seen_ids.add(item_id)
                deduplicated.append(item)
            elif not item_id:
                # Keep items without IDs (shouldn't happen but be safe)
                deduplicated.append(item)
        
        return deduplicated
    
    def get_queue_stats(self) -> Dict:
        """Get statistics about the current queue (ES or legacy)."""
        if self.es_queue:
            return self.es_queue.get_queue_stats()
        else:
            # Legacy file-based stats
            queue = self.load_queue()
            
            stats = {
                "total_techniques": len(queue.get("techniques", [])),
                "total_cves": len(queue.get("cves", [])),
                "total_threats": len(queue.get("threats", [])),
                "total_news_articles": len(queue.get("news_articles", [])),
                "total_threat_intelligence": len(queue.get("threat_intelligence", [])),
                "total_advisories": len(queue.get("advisories", [])),
                "last_updated": queue.get("metadata", {}).get("last_updated", "unknown"),
                "sources": {}
            }
            
            # Count items by source from all categories
            all_items = (queue.get("techniques", []) + queue.get("cves", []) + 
                        queue.get("news_articles", []) + queue.get("threat_intelligence", []) + 
                        queue.get("advisories", []))
            
            for item in all_items:
                source = item.get("source", "unknown")
                stats["sources"][source] = stats["sources"].get(source, 0) + 1
                
            return stats
    
    def clear_queue(self):
        """Clear the research queue (ES or legacy)."""
        if self.es_queue:
            cleared_count = self.es_queue.clear_queue()
            self.logger.info(f"🗑️ Elasticsearch queue cleared: {cleared_count} items")
        else:
            empty_queue = {"techniques": [], "cves": [], "threats": [], "metadata": {}}
            self.save_queue(empty_queue)
            self.logger.info("🗑️ Legacy research queue cleared")
    
    def export_queue(self, output_file: str):
        """Export queue to specified file (ES or legacy)."""
        if self.es_queue:
            try:
                exported_file = self.es_queue.export_queue(output_file)
                self.logger.info(f"📁 Elasticsearch queue exported to {exported_file}")
            except Exception as e:
                self.logger.error(f"Could not export ES queue: {e}")
        else:
            queue = self.load_queue()
            try:
                with open(output_file, 'w') as f:
                    json.dump(queue, f, indent=2)
                self.logger.info(f"📁 Legacy queue exported to {output_file}")
            except Exception as e:
                self.logger.error(f"Could not export legacy queue: {e}")


def main():
    """Main CLI interface."""
    parser = argparse.ArgumentParser(description="Research Manager - Autonomous Research System")
    parser.add_argument("command", choices=[
        "populate", "stats", "build", "autonomous", "clear", "export", "test",
        "es-stats", "es-pending", "es-retry", "es-status",
        "custom-add", "custom-list", "custom-search", "custom-cluster", "custom-stats", "custom-export"
    ], help="Command to execute")
    
    parser.add_argument("--force", action="store_true", 
                       help="Force refresh even if recent data exists")
    parser.add_argument("--max-items", type=int, 
                       help="Maximum items to process (for build command)")
    parser.add_argument("--output", type=str, 
                       help="Output file (for export command)")
    parser.add_argument("--type", type=str,
                       help="Item type filter (for ES commands)")
    parser.add_argument("--platform", type=str,
                       help="Platform filter (for ES commands)")
    
    args = parser.parse_args()
    
    # Create manager
    try:
        manager = ResearchQueueManager()
    except Exception as e:
        print(f"❌ Could not initialize research manager: {e}")
        return 1
    
    if args.command == "test":
        print("🧪 Testing system structure...")
        print(f"✅ Research manager initialized")
        print(f"✅ Data directories: {Path('data/queue').exists()}")
        print(f"✅ Feeds available: {FEEDS_AVAILABLE}")
        print(f"✅ Config available: {CONFIG_AVAILABLE}")
        stats = manager.get_queue_stats()
        if manager.es_queue:
            total_items = stats.get('total_items', 0)
            techniques = stats.get('by_type', {}).get('technique', 0)
            print(f"✅ Elasticsearch queue accessible: {total_items} total items, {techniques} techniques")
        else:
            techniques = stats.get('total_techniques', 0)
            print(f"✅ Legacy queue accessible: {techniques} techniques")
        return 0
        
    elif args.command == "populate":
        print("📥 Populating research queue from all sources...")
        queue = manager.populate_from_all_sources(force_refresh=args.force)
        stats = manager.get_queue_stats()
        
        if manager.es_queue:
            # Elasticsearch format
            total_items = stats.get('total_items', 0)
            techniques = stats.get('by_type', {}).get('technique', 0)
            news_articles = stats.get('by_type', {}).get('news_articles', 0)
            threat_intel = stats.get('by_type', {}).get('threat_intelligence', 0)
            advisories = stats.get('by_type', {}).get('advisories', 0)
            cves = stats.get('by_type', {}).get('cves', 0)
            
            print(f"✅ Queue populated: {total_items} total items")
            print(f"   📋 {techniques} techniques, {cves} CVEs")
            print(f"   📰 {news_articles} articles, {threat_intel} threat intel")
            print(f"   🔒 {advisories} advisories")
        else:
            # Legacy format
            total_items = (stats['total_techniques'] + stats['total_cves'] + stats['total_threats'] + 
                          stats['total_news_articles'] + stats['total_threat_intelligence'] + stats['total_advisories'])
            print(f"✅ Queue populated: {total_items} total items")
            print(f"   📋 {stats['total_techniques']} techniques, {stats['total_cves']} CVEs")
            print(f"   📰 {stats['total_news_articles']} articles, {stats['total_threat_intelligence']} threat intel")
            print(f"   🔒 {stats['total_advisories']} advisories")
        
    elif args.command == "stats":
        print("📊 Research Queue Statistics:")
        stats = manager.get_queue_stats()
        print(f"  Total Techniques: {stats['total_techniques']}")
        print(f"  Total CVEs: {stats['total_cves']}")
        print(f"  Total Threats: {stats['total_threats']}")
        print(f"  Total News Articles: {stats['total_news_articles']}")
        print(f"  Total Threat Intelligence: {stats['total_threat_intelligence']}")
        print(f"  Total Advisories: {stats['total_advisories']}")
        total_items = (stats['total_techniques'] + stats['total_cves'] + stats['total_threats'] + 
                      stats['total_news_articles'] + stats['total_threat_intelligence'] + stats['total_advisories'])
        print(f"  📋 Total Items: {total_items}")
        print(f"  Last Updated: {stats['last_updated']}")
        print("  Sources:")
        for source, count in stats['sources'].items():
            print(f"    {source}: {count}")
            
    elif args.command == "clear":
        print("🗑️  Clearing research queue...")
        manager.clear_queue()
        print("✅ Queue cleared")
        
    elif args.command == "export":
        output_file = args.output or f"queue_export_{int(time.time())}.json"
        print(f"📁 Exporting queue to {output_file}...")
        manager.export_queue(output_file)
        print("✅ Export complete")
    
    elif args.command == "es-stats":
        if manager.es_queue:
            print("📊 Elasticsearch Queue Statistics:")
            stats = manager.es_queue.get_queue_stats()
            print(f"  Total Items: {stats.get('total_items', 0)}")
            print("  By Status:")
            for status, count in stats.get('by_status', {}).items():
                print(f"    {status}: {count}")
            print("  By Type:")
            for item_type, count in stats.get('by_type', {}).items():
                print(f"    {item_type}: {count}")
            print("  By Platform:")
            for platform, count in stats.get('by_platform', {}).items():
                print(f"    {platform}: {count}")
        else:
            print("❌ Elasticsearch queue not available")
    
    elif args.command == "es-pending":
        if manager.es_queue:
            print("📋 Pending Queue Items:")
            items = manager.es_queue.get_pending_items(
                item_type=args.type,
                platform=args.platform,
                limit=args.max_items or 10
            )
            for item in items:
                print(f"  {item['id']} ({item['type']}) - {item['title']}")
        else:
            print("❌ Elasticsearch queue not available")
    
    elif args.command == "es-retry":
        if manager.es_queue:
            print("🔄 Retrying failed items...")
            retried = manager.es_queue.retry_failed_items()
            print(f"✅ Reset {retried} failed items to pending")
        else:
            print("❌ Elasticsearch queue not available")
    
    elif args.command == "es-status":
        if manager.es_queue:
            print("🔧 System Status:")
            status = manager.es_queue.get_system_status()
            for component, info in status.items():
                print(f"  {component}: {info.get('status', 'unknown')}")
                if 'last_updated' in info:
                    print(f"    Last Updated: {info['last_updated']}")
        else:
            print("❌ Elasticsearch queue not available")
    
    elif args.command == "build":
        print("🤖 Running autonomous research/build process...")
        if CONFIG_AVAILABLE:
            try:
                # Import AutonomousResearchSystem locally to ensure availability
                from src.autonomous_research.core.autonomous_system import AutonomousResearchSystem
                autonomous_system = AutonomousResearchSystem(project_root=str(project_root))
                # Run a single autonomous research/build cycle
                cycle_stats = autonomous_system.run_single_cycle()
                print(f"✅ Autonomous research/build complete.")
                print(f"   Techniques processed: {cycle_stats['techniques_processed']}")
                print(f"   Content generated: {cycle_stats['content_generated']}")
                print(f"   Research conducted: {cycle_stats['research_conducted']}")
                print(f"   Duration: {cycle_stats['duration']:.1f}s")
            except Exception as e:
                print(f"❌ Error running autonomous research system: {e}")
        else:
            print("⚠️  Autonomous research system not available (missing config/modules)")
    
    elif args.command == "custom-add":
        handle_custom_add(args)
    elif args.command == "custom-list":
        handle_custom_list(args)
    elif args.command == "custom-search":
        handle_custom_search(args)
    elif args.command == "custom-cluster":
        handle_custom_cluster(args)
    elif args.command == "custom-stats":
        handle_custom_stats(args)
    elif args.command == "custom-export":
        handle_custom_export(args)
    
    else:
        print(f"⚠️  Command '{args.command}' not fully implemented yet")
        print("Available: test, populate, stats, clear, export, build")
        print("ES Commands: es-stats, es-pending, es-retry, es-status")
        print("Custom Techniques: custom-add, custom-list, custom-search, custom-cluster, custom-stats, custom-export")


def handle_custom_add(args):
    """Handle adding a custom technique."""
    if not custom_tech_available:
        print("❌ Custom techniques module not available")
        return
    
    manager = CustomTechniqueManager(str(project_root))
    
    # Interactive input if not provided
    if not hasattr(args, 'name') or not args.name:
        args.name = input("Technique name: ")
    if not hasattr(args, 'description') or not args.description:
        args.description = input("Description: ")
    if not hasattr(args, 'category') or not args.category:
        print("Available categories: emerging_threat, tool_specific, procedural_cluster, zero_day, living_off_land, industry_specific")
        args.category = input("Category: ")
    
    technique = CustomTechnique(
        id="",  # Auto-generated
        name=args.name,
        description=args.description,
        category=args.category,
        platforms=getattr(args, 'platforms', "").split(',') if getattr(args, 'platforms', "") else None,
        severity=getattr(args, 'severity', 'medium'),
        sources=getattr(args, 'sources', "").split(',') if getattr(args, 'sources', "") else None,
        tags=getattr(args, 'tags', "").split(',') if getattr(args, 'tags', "") else None
    )
    
    technique_id = manager.add_custom_technique(technique)
    print(f"✅ Added custom technique: {technique_id}")


def handle_custom_list(args):
    """Handle listing custom techniques."""
    if not custom_tech_available:
        print("❌ Custom techniques module not available")
        return
    
    manager = CustomTechniqueManager(str(project_root))
    
    category = getattr(args, 'category', None)
    if category:
        techniques = manager.get_techniques_by_category(category)
        print(f"📋 Custom Techniques in category '{category}':")
    else:
        techniques = list(manager.custom_techniques.values())
        print(f"📋 All Custom Techniques:")
    
    if not techniques:
        print("   No techniques found")
        return
    
    for technique in techniques[:getattr(args, 'max_items', 20)]:
        print(f"  {technique.id} - {technique.name}")
        print(f"    Category: {technique.category}")
        print(f"    Severity: {technique.severity}")
        if technique.platforms:
            print(f"    Platforms: {', '.join(technique.platforms)}")
        print()


def handle_custom_search(args):
    """Handle searching custom techniques."""
    if not custom_tech_available:
        print("❌ Custom techniques module not available")
        return
    
    manager = CustomTechniqueManager(str(project_root))
    
    query = getattr(args, 'query', None)
    if not query:
        query = input("Search query: ")
    
    category = getattr(args, 'category', None)
    results = manager.search_custom_techniques(query, category)
    
    print(f"🔍 Search results for '{query}':")
    if not results:
        print("   No results found")
        return
    
    for technique in results:
        print(f"  {technique.id} - {technique.name}")
        print(f"    {technique.description[:100]}...")
        print(f"    Category: {technique.category}, Severity: {technique.severity}")
        print()


def handle_custom_cluster(args):
    """Handle creating procedural clusters."""
    if not custom_tech_available:
        print("❌ Custom techniques module not available")
        return
    
    manager = CustomTechniqueManager(str(project_root))
    
    # Example clusters from Swedish data
    if getattr(args, 'example', False):
        print("🎯 Creating example procedural clusters...")
        
        # Example 1 - Memory Injection
        memory_injection_text = """
        The payload decompresses executable code in memory using advanced compression techniques.
        It then injects the code into target processes using process hollowing and thread hijacking methods.
        The injected code operates within legitimate process contexts to maintain stealth and avoid detection.
        """
        
        # Example 2 - Data Collection
        data_collection_text = """
        The system enumerates network configurations and installed software packages systematically.
        It compiles comprehensive system information including running processes, services, and security tools.
        The collected data is prepared for exfiltration through encrypted communication channels.
        """
        
        memory_cluster_id = manager.create_procedural_cluster_from_text(
            memory_injection_text, "Memory Injection Procedures"
        )
        data_cluster_id = manager.create_procedural_cluster_from_text(
            data_collection_text, "Data Collection Procedures"
        )
        
        print(f"✅ Created memory injection cluster: {memory_cluster_id}")
        print(f"✅ Created data collection cluster: {data_cluster_id}")
        
    else:
        # Interactive cluster creation
        text = input("Enter procedural text (or file path): ")
        if Path(text).exists():
            with open(text, 'r') as f:
                text = f.read()
        
        name = input("Cluster name (optional): ") or None
        cluster_id = manager.create_procedural_cluster_from_text(text, name)
        print(f"✅ Created procedural cluster: {cluster_id}")


def handle_custom_stats(args):
    """Handle showing custom techniques statistics."""
    if not custom_tech_available:
        print("❌ Custom techniques module not available")
        return
    
    manager = CustomTechniqueManager(str(project_root))
    stats = manager.get_stats()
    
    print("📊 Custom Techniques Statistics:")
    print(f"  Total Custom Techniques: {stats['total_custom_techniques']}")
    print(f"  Total Procedural Clusters: {stats['total_procedural_clusters']}")
    
    if stats['techniques_by_category']:
        print("\n  Techniques by Category:")
        for category, count in stats['techniques_by_category'].items():
            print(f"    {category}: {count}")
    
    if stats['techniques_by_severity']:
        print("\n  Techniques by Severity:")
        for severity, count in stats['techniques_by_severity'].items():
            print(f"    {severity}: {count}")
    
    if stats['total_procedural_clusters'] > 0:
        print(f"\n  Average Cluster Coherence: {stats['average_cluster_coherence']:.3f}")


def handle_custom_export(args):
    """Handle exporting custom techniques to Elasticsearch."""
    if not custom_tech_available:
        print("❌ Custom techniques module not available")
        return
    
    manager = CustomTechniqueManager(str(project_root))
    es_docs = manager.export_to_elasticsearch_format()
    
    if getattr(args, 'to_es', False) and CONFIG_AVAILABLE:
        # Export to Elasticsearch
        try:
            es_queue = ElasticsearchQueueManager()
            count = 0
            for doc in es_docs:
                # Add to queue with custom type
                es_queue.add_to_queue([doc], item_type=doc['type'], source="custom_techniques")
                count += 1
            print(f"✅ Exported {count} custom techniques/clusters to Elasticsearch")
        except Exception as e:
            print(f"❌ Error exporting to Elasticsearch: {e}")
    else:
        # Export to JSON file
        output_file = getattr(args, 'output', 'custom_techniques_export.json')
        with open(output_file, 'w') as f:
            json.dump(es_docs, f, indent=2)
        print(f"✅ Exported {len(es_docs)} items to {output_file}")


def setup_custom_techniques_args(subparsers):
    """Setup argument parsers for custom techniques commands."""
    
    # Custom technique add
    add_parser = subparsers.add_parser('custom-add', help='Add a custom technique')
    add_parser.add_argument('--name', help='Technique name')
    add_parser.add_argument('--description', help='Technique description')
    add_parser.add_argument('--category', help='Technique category')
    add_parser.add_argument('--platforms', help='Comma-separated platforms')
    add_parser.add_argument('--severity', choices=['low', 'medium', 'high', 'critical'], default='medium')
    add_parser.add_argument('--sources', help='Comma-separated sources')
    add_parser.add_argument('--tags', help='Comma-separated tags')
    
    # Custom technique list
    list_parser = subparsers.add_parser('custom-list', help='List custom techniques')
    list_parser.add_argument('--category', help='Filter by category')
    list_parser.add_argument('--max-items', type=int, default=20, help='Maximum items to show')
    
    # Custom technique search
    search_parser = subparsers.add_parser('custom-search', help='Search custom techniques')
    search_parser.add_argument('--query', help='Search query')
    search_parser.add_argument('--category', help='Filter by category')
    
    # Procedural cluster
    cluster_parser = subparsers.add_parser('custom-cluster', help='Create procedural clusters')
    cluster_parser.add_argument('--example', action='store_true', help='Create example procedural clusters')
    
    # Custom stats
    subparsers.add_parser('custom-stats', help='Show custom techniques statistics')
    
    # Custom export
    export_parser = subparsers.add_parser('custom-export', help='Export custom techniques')
    export_parser.add_argument('--to-es', action='store_true', help='Export to Elasticsearch')
    export_parser.add_argument('--output', default='custom_techniques_export.json', help='Output file')


def setup_argument_parser():
    """Setup the argument parser with all commands."""
    parser = argparse.ArgumentParser(description="Research Manager CLI")
    
    # Add main arguments
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    parser.add_argument('--project-root', default=str(project_root), help='Project root directory')
    
    # Create subparsers
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Existing command parsers...
    subparsers.add_parser('test', help='Test system connectivity and functionality')
    
    populate_parser = subparsers.add_parser('populate', help='Populate research queue from feeds')
    populate_parser.add_argument('--max-techniques', type=int, help='Maximum techniques to add')
    populate_parser.add_argument('--max-cves', type=int, help='Maximum CVEs to add')
    populate_parser.add_argument('--max-news', type=int, help='Maximum news articles to add')
    
    stats_parser = subparsers.add_parser('stats', help='Show queue statistics')
    stats_parser.add_argument('--format', choices=['summary', 'detailed'], default='summary')
    
    subparsers.add_parser('clear', help='Clear research queue (use with caution)')
    
    export_parser = subparsers.add_parser('export', help='Export research queue')
    export_parser.add_argument('--format', choices=['json', 'csv'], default='json')
    export_parser.add_argument('--output', help='Output file path')
    
    build_parser = subparsers.add_parser('build', help='Run autonomous research/build')
    build_parser.add_argument('--max-items', type=int, help='Maximum items to process')
    
    # Elasticsearch-specific commands
    subparsers.add_parser('es-stats', help='Show Elasticsearch queue statistics')
    
    es_pending_parser = subparsers.add_parser('es-pending', help='Show pending items in ES queue')
    es_pending_parser.add_argument('--type', help='Filter by item type')
    es_pending_parser.add_argument('--platform', help='Filter by platform')
    es_pending_parser.add_argument('--max-items', type=int, default=10, help='Maximum items to show')
    
    es_retry_parser = subparsers.add_parser('es-retry', help='Retry failed items in ES queue')
    es_retry_parser.add_argument('--max-retries', type=int, default=3, help='Maximum retry attempts')
    
    es_status_parser = subparsers.add_parser('es-status', help='Show detailed ES queue status')
    es_status_parser.add_argument('--item-id', help='Show status for specific item')
    
    # Custom techniques commands
    if custom_tech_available:
        setup_custom_techniques_args(subparsers)
    
    return parser


def main():
    """Main CLI entry point."""
    parser = setup_argument_parser()
    args = parser.parse_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Handle different commands
    if args.command == "test":
        handle_test_command()
    elif args.command == "populate":
        handle_populate_command(args)
    elif args.command == "stats":
        handle_stats_command(args)
    elif args.command == "clear":
        handle_clear_command()
    elif args.command == "export":
        handle_export_command(args)
    elif args.command == "es-stats":
        handle_es_stats_command(args)
    elif args.command == "es-pending":
        handle_es_pending_command(args)
    elif args.command == "es-retry":
        handle_es_retry_command(args)
    elif args.command == "es-status":
        handle_es_status_command(args)
    elif args.command == "build":
        # Run autonomous research/build
        if hasattr(args, 'max_items') and args.max_items:
            print(f"🎯 Processing maximum {args.max_items} items")
        print("🤖 Running autonomous research/build process...")
        if CONFIG_AVAILABLE:
            try:
                # Import AutonomousResearchSystem locally to ensure availability
                from src.autonomous_research.core.autonomous_system import AutonomousResearchSystem
                autonomous_system = AutonomousResearchSystem(project_root=str(project_root))
                # Run a single autonomous research/build cycle
                cycle_stats = autonomous_system.run_single_cycle()
                print(f"✅ Autonomous research/build complete.")
                print(f"   Techniques processed: {cycle_stats['techniques_processed']}")
                print(f"   Content generated: {cycle_stats['content_generated']}")
                print(f"   Research conducted: {cycle_stats['research_conducted']}")
                print(f"   Duration: {cycle_stats['duration']:.1f}s")
            except Exception as e:
                print(f"❌ Error running autonomous research: {e}")
        else:
            print("❌ Configuration not available for autonomous research")


if __name__ == "__main__":
    main()
