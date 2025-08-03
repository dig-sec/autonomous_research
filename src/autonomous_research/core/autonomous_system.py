#!/usr/bin/env python3
"""
Autonomous Research System

The main autonomous system that coordinates research, content generation,
and knowledge base maintenance.
"""

import os
import json
import time
import logging
import yaml
import signal
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path
from elasticsearch import Elasticsearch

from autonomous_research.research.summary_manager import ResearchSummaryManager
from autonomous_research.research.external_research import ExternalResearcher
from autonomous_research.generation.content_generator import ContentGenerator
from autonomous_research.core.project_manager import ProjectManager
from autonomous_research.core.status_manager import StatusManager
from autonomous_research.core.elasticsearch_queue_manager import ElasticsearchQueueManager
from autonomous_research.research.academic_sources import AcademicSources
from autonomous_research.rag import StandaloneElasticsearchRAG
from autonomous_research.config.secure_config import load_config, get_elasticsearch_config
from autonomous_research.knowledge.custom_techniques import CustomTechniqueManager
import sys
sys.path.append('.')
from autonomous_research.utils.loop_detector import LoopDetector


class AutonomousResearchSystem:
    """
    Main autonomous research system that orchestrates all components.
    
    Features:
    - Autonomous research scheduling
    - Multi-source content generation
    - Quality validation and improvement
    - Knowledge base maintenance
    """

    def __init__(
        self,
        project_root: str = ".",
        model: Optional[str] = None,
        update_interval: Optional[int] = None,
        config_path: Optional[str] = "config/config.yaml",
    ):
        self.project_root = Path(project_root)
        # Use secure_config loader for config
        from autonomous_research.config.secure_config import load_config
        config = load_config(config_path or "config/config.yaml")
        es_conf = config.get("elasticsearch", {})
        rag_conf = config.get("rag", {})
        academic_conf = config.get("academic_sources", {})
        agent_conf = config.get("agent", {})
        self.model = model or agent_conf.get("model", "llama2-uncensored:7b")
        self.update_interval = update_interval or agent_conf.get("update_interval", 10)  # 10 seconds for faster cycles
        
        # Initialize logging
        self.logger = self._setup_logging()
        
        # Initialize core components
        self.project_manager = ProjectManager(project_root)
        self.status_manager = StatusManager(project_root)
        self.research_manager = ResearchSummaryManager(project_root)
        self.content_generator = ContentGenerator(self.model)
        self.external_researcher = ExternalResearcher()
        
        # Initialize Elasticsearch queue manager
        try:
            self.es_queue = ElasticsearchQueueManager()
            self.logger.info("✅ Elasticsearch queue manager initialized")
        except Exception as e:
            self.logger.warning(f"Could not initialize Elasticsearch queue: {e}")
            self.es_queue = None
        
        # Academic and RAG integration - use secure config
        es_config = get_elasticsearch_config()
        self.academic_sources = AcademicSources()
        self.rag = StandaloneElasticsearchRAG(
            embedding_model=rag_conf.get("embedding_model", "all-MiniLM-L6-v2"),
            elasticsearch_host=es_config["host"],
            elasticsearch_port=es_config["port"],
            elasticsearch_user=es_config["user"],
            elasticsearch_password=es_config["password"]
        )
        self.es = Elasticsearch(
            hosts=[{
                "host": es_config["host"],
                "port": es_config["port"],
                "scheme": "http"
            }],
            http_auth=(es_config["user"], es_config["password"])
        )
        self.output_index = es_conf.get("output_index", "autonomous_research_outputs")
        self.arxiv_max_results = academic_conf.get("arxiv_max_results", 3)
        self.scholar_max_results = academic_conf.get("scholar_max_results", 3)
        
        # Initialize custom techniques manager
        try:
            self.custom_techniques = CustomTechniqueManager()
            self.logger.info("✅ Custom techniques manager initialized")
        except Exception as e:
            self.logger.warning(f"Could not initialize custom techniques manager: {e}")
            self.custom_techniques = None
        
        # Initialize loop detector
        self.loop_detector = LoopDetector(history_size=20, repeat_threshold=3)
        
        # Initialize shutdown flag
        self.shutdown_requested = False
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        self.logger.info("Autonomous Research System initialized")

    def _setup_logging(self) -> logging.Logger:
        """Set up logging configuration."""
        log_file = self.project_root / "logs" / "autonomous_research.log"
        log_file.parent.mkdir(exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(),
            ],
        )
        return logging.getLogger(__name__)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        self.logger.info(f"Received signal {signum}, requesting shutdown...")
        self.shutdown_requested = True

    def identify_research_needs(self) -> List[Dict]:
        """Identify techniques that need research or updates using ES queue or legacy status."""
        if self.es_queue:
            # Use Elasticsearch queue to get pending items
            pending_items = self.es_queue.get_pending_items(item_type="techniques", limit=100)
            needs_research = []
            
            for item in pending_items:
                # Convert ES item format to legacy format for compatibility
                technique = {
                    "id": item["id"],
                    "platform": item.get("platform", "windows"),
                    "status": item["status"],
                    "data": item.get("data", {})
                }
                # Add any additional fields from original data
                if "data" in item and isinstance(item["data"], dict):
                    technique.update(item["data"])
                
                needs_research.append(technique)
            
            return needs_research
        else:
            # Legacy status-based approach
            status = self.status_manager.load_status()
            needs_research = []
            
            for technique in status["techniques"]:
                if technique.get("status") == "pending":
                    needs_research.append(technique)
                elif "last_updated" in technique:
                    last_updated = datetime.fromisoformat(technique["last_updated"])
                    if datetime.now() - last_updated > timedelta(days=30):
                        needs_research.append(technique)
                        
            return needs_research

    def conduct_research(self, technique: Dict) -> str:
        """Conduct comprehensive research for a technique, including academic sources and RAG ingestion."""
        technique_id = technique["id"]
        platform = technique.get("platform", "windows").lower()
        
        self.logger.info(f"Conducting research for {technique_id}")
        
        # Check for existing research
        existing_summary = self.research_manager.get_summary(technique_id, platform)
        if existing_summary and not self._needs_research_update(existing_summary):
            self.logger.info(f"Using cached research for {technique_id}")
            return existing_summary.summary
        
        # Gather fresh research
        research_contexts = []
        sources = []
        
        # Get external research
        external_context, external_sources = self.external_researcher.research_technique(
            technique_id, platform
        )
        if external_context:
            research_contexts.append(external_context)
            sources.extend(external_sources)
        
        # Get academic research and ingest into RAG
        academic_results = self.academic_sources.fetch_arxiv(technique_id, max_results=self.arxiv_max_results)
        academic_results += self.academic_sources.fetch_google_scholar(technique_id, max_results=self.scholar_max_results)
        normalized_academic = self.academic_sources.normalize_results(academic_results, query=technique_id)
        for paper in normalized_academic:
            content = f"{paper['title']}\n\n{paper['summary']}\nAuthors: {', '.join(paper['authors'])}\nLink: {paper['link']}"
            self.rag.add_document_from_text(content, title=paper['title'], source="academic", source_type="research")
            research_contexts.append(content)
            sources.append("academic")
        
        # Create or update summary
        if research_contexts:
            summary = self.research_manager.update_summary(
                technique_id, platform, research_contexts, sources
            )
            self.logger.info(f"Created research summary for {technique_id}")
            # Store output in Elasticsearch
            self.store_output_in_elasticsearch(technique_id, platform, summary)
            return summary.summary
        else:
            self.logger.warning(f"No research context found for {technique_id}")
            return ""

    def _needs_research_update(self, summary) -> bool:
        """Check if research summary needs updating."""
        # Update if older than 7 days or confidence is low
        age_days = (datetime.now() - summary.last_updated).days
        return age_days > 7 or summary.confidence_score < 7.0

    def generate_content(self, technique: Dict, research_context: str, shutdown_flag=None):
        """Generate all content files for a technique, with shutdown checks."""
        technique_id = technique["id"]
        platform = technique.get("platform", "windows").lower()
        self.logger.info(f"Generating content for {technique_id}")
        output_base = self.project_root / "output" / platform / "techniques" / technique_id
        output_base.mkdir(parents=True, exist_ok=True)
        if shutdown_flag and shutdown_flag():
            self.logger.info("Shutdown requested before content generation, aborting.")
            return False
        success_count = self.content_generator.generate_technique_content(
            technique, research_context, output_base, shutdown_flag=shutdown_flag
        )
        if shutdown_flag and shutdown_flag():
            self.logger.info("Shutdown requested after content generation, aborting.")
            return False
        self.logger.info(f"Generated {success_count} files for {technique_id} in output/{platform}/techniques/{technique_id}")
        return success_count > 0

    def update_technique_status(self, technique_id: str, platform: Optional[str] = None):
        """Update technique status to completed in ES queue or legacy status."""
        if self.es_queue:
            # Update in Elasticsearch queue
            self.es_queue.update_item_status(technique_id, "completed")
            self.logger.debug(f"Updated {technique_id} status to completed in ES queue")
        else:
            # Legacy status update
            status = self.status_manager.load_status()
            
            for technique in status["techniques"]:
                if technique["id"] == technique_id:
                    technique["status"] = "completed"
                    technique["last_updated"] = datetime.now().isoformat()
                    break
                    
            self.status_manager.save_status(status)

    def run_single_cycle(self) -> Dict:
        """Run a single research and generation cycle with shutdown checks."""
        cycle_stats = {
            "techniques_processed": 0,
            "content_generated": 0,
            "research_conducted": 0,
            "start_time": datetime.now(),
        }
        techniques_to_research = self.identify_research_needs()
        self.logger.info(f"Found {len(techniques_to_research)} techniques needing research")
        for technique in techniques_to_research:
            if self.shutdown_requested:
                self.logger.info("Shutdown requested, stopping cycle early.")
                break
            technique_id = technique["id"]
            if self.loop_detector.is_looping(technique_id):
                self.logger.warning(f"Skipping {technique_id} - loop detected")
                continue
            self.loop_detector.add_item(technique_id)
            try:
                research_context = self.conduct_research(technique)
                if self.shutdown_requested:
                    self.logger.info("Shutdown requested after research, stopping.")
                    break
                if research_context:
                    cycle_stats["research_conducted"] += 1
                    if self.generate_content(technique, research_context, shutdown_flag=lambda: self.shutdown_requested):
                        cycle_stats["content_generated"] += 1
                        self.update_technique_status(technique_id, technique.get("platform", "unknown"))
                cycle_stats["techniques_processed"] += 1
            except Exception as e:
                self.logger.error(f"Error processing {technique_id}: {e}")
        cycle_stats["end_time"] = datetime.now()
        cycle_stats["duration"] = (cycle_stats["end_time"] - cycle_stats["start_time"]).total_seconds()
        return cycle_stats

    def run_autonomous(self, max_empty_cycles=2):  # Faster feed refresh after 2 empty cycles
        """Run the autonomous research system continuously."""
        self.logger.info("Starting autonomous research mode")
        empty_cycles = 0
        
        try:
            while not self.shutdown_requested:
                cycle_stats = self.run_single_cycle()
                
                # Check if we processed any techniques
                if cycle_stats['techniques_processed'] == 0:
                    empty_cycles += 1
                    self.logger.info(f"Empty cycle {empty_cycles}/{max_empty_cycles}")
                    
                    if empty_cycles >= max_empty_cycles:
                        self.logger.info("Multiple empty cycles detected, refreshing feeds...")
                        self.refresh_feeds()
                        empty_cycles = 0
                else:
                    empty_cycles = 0  # Reset counter if we processed something
                
                self.logger.info(
                    f"Cycle completed: {cycle_stats['techniques_processed']} processed, "
                    f"{cycle_stats['content_generated']} generated, "
                    f"{cycle_stats['duration']:.1f}s"
                )
                
                if not self.shutdown_requested:
                    self.logger.info(f"Sleeping for {self.update_interval} seconds...")
                    # Sleep in smaller chunks to respond to shutdown requests faster
                    sleep_chunk = min(2, self.update_interval)  # Sleep in 2-second chunks max for faster response
                    elapsed = 0
                    while elapsed < self.update_interval and not self.shutdown_requested:
                        time.sleep(sleep_chunk)
                        elapsed += sleep_chunk
                
        except KeyboardInterrupt:
            self.logger.info("Autonomous research stopped by user")
        except Exception as e:
            self.logger.error(f"Autonomous research error: {e}")
            raise
        finally:
            self.logger.info("Autonomous research system shutdown complete")

    def get_system_status(self) -> Dict:
        """Get comprehensive system status."""
        status = self.status_manager.load_status()
        research_summaries = self.research_manager.get_all_summaries()
        
        system_status = {
            "total_techniques": len(status["techniques"]),
            "completed_techniques": len([t for t in status["techniques"] if t.get("status") == "completed"]),
            "pending_techniques": len([t for t in status["techniques"] if t.get("status") == "pending"]),
            "research_summaries": len(research_summaries),
            "last_updated": status.get("last_updated"),
            "system_version": "2.0.0",
        }
        
        # Add custom techniques stats if available
        if self.custom_techniques:
            try:
                custom_stats = self.custom_techniques.get_stats()
                system_status["custom_techniques"] = custom_stats
            except Exception as e:
                self.logger.warning(f"Could not get custom techniques stats: {e}")
        
        return system_status

    def process_custom_techniques(self):
        """Process custom techniques and add them to the research queue."""
        if not self.custom_techniques:
            self.logger.warning("Custom techniques manager not available")
            return
        
        try:
            # Get all custom techniques
            all_techniques = list(self.custom_techniques.custom_techniques.values())
            technique_items = []
            
            for technique in all_techniques:
                # Convert custom technique to queue item format
                queue_item = {
                    "id": technique.id,
                    "name": technique.name,
                    "description": technique.description,
                    "platform": technique.platforms[0] if technique.platforms else "multi",
                    "category": technique.category,
                    "severity": technique.severity,
                    "status": "pending",
                    "source": "custom_techniques",
                    "data": {
                        "subcategory": technique.subcategory,
                        "detection_difficulty": technique.detection_difficulty,
                        "sources": technique.sources,
                        "tags": technique.tags,
                        "related_mitre_techniques": technique.related_mitre_techniques,
                        "metadata": technique.metadata
                    }
                }
                technique_items.append(queue_item)
            
            # Add techniques to ES queue in batch
            if self.es_queue and technique_items:
                try:
                    self.es_queue.add_to_queue(technique_items, item_type="custom_technique")
                    self.logger.info(f"Added {len(technique_items)} custom techniques to research queue")
                except Exception as e:
                    self.logger.warning(f"Could not add custom techniques to queue: {e}")
            
            # Also process procedural clusters
            all_clusters = list(self.custom_techniques.procedural_clusters.values())
            cluster_items = []
            
            for cluster in all_clusters:
                cluster_item = {
                    "id": cluster.cluster_id,  # Use correct attribute name
                    "name": cluster.name,
                    "description": f"Procedural cluster analysis: {cluster.description}",
                    "platform": "multi",
                    "category": "procedural_cluster", 
                    "severity": "medium",
                    "status": "pending",
                    "source": "custom_techniques_cluster",
                    "data": {
                        "procedures": cluster.procedures,
                        "coherence_score": cluster.coherence_score,
                        "cluster_metadata": cluster.metadata,
                        "cosine_distances": cluster.cosine_distances,
                        "centroid_procedure": cluster.centroid_procedure,
                        "cluster_size": cluster.cluster_size
                    }
                }
                cluster_items.append(cluster_item)
            
            # Add clusters to ES queue in batch
            if self.es_queue and cluster_items:
                try:
                    self.es_queue.add_to_queue(cluster_items, item_type="procedural_cluster")
                    self.logger.info(f"Added {len(cluster_items)} procedural clusters to research queue")
                except Exception as e:
                    self.logger.warning(f"Could not add clusters to queue: {e}")
                        
        except Exception as e:
            self.logger.error(f"Error processing custom techniques: {e}")

    def export_custom_techniques_to_elasticsearch(self):
        """Export custom techniques directly to Elasticsearch for RAG integration."""
        if not self.custom_techniques:
            return
        
        try:
            # Export custom techniques in Elasticsearch format
            es_docs = self.custom_techniques.export_to_elasticsearch_format()
            
            for doc in es_docs:
                # Index in both custom techniques index and RAG index
                try:
                    # Store in custom techniques index
                    self.es.index(
                        index="custom_techniques",
                        id=doc["id"],
                        body=doc
                    )
                    
                    # Also add to RAG system for semantic search
                    content = f"{doc['name']}\n\n{doc['description']}\n\nCategory: {doc['category']}\nSeverity: {doc['severity']}"
                    if doc.get('tags'):
                        content += f"\nTags: {', '.join(doc['tags'])}"
                    
                    self.rag.add_document_from_text(
                        content,
                        title=doc['name'],
                        source="custom_techniques",
                        source_type=doc['category']
                    )
                    
                    self.logger.info(f"Exported custom technique {doc['id']} to Elasticsearch")
                    
                except Exception as e:
                    self.logger.warning(f"Could not export technique {doc['id']}: {e}")
                    
        except Exception as e:
            self.logger.error(f"Error exporting custom techniques: {e}")

    def store_output_in_elasticsearch(self, technique_id, platform, summary_obj):
        """Store research summary output JSON in Elasticsearch index."""
        doc = {
            "technique_id": technique_id,
            "platform": platform,
            "summary": summary_obj.summary,
            "sources": summary_obj.sources,
            "confidence_score": summary_obj.confidence_score,
            "last_updated": summary_obj.last_updated.isoformat(),
            "source_count": summary_obj.source_count,
            "research_depth": summary_obj.research_depth,
        }
        self.es.index(index=self.output_index, id=f"{technique_id}_{platform}", body=doc)

    def get_output_from_elasticsearch(self, technique_id=None, platform=None, min_confidence=None, max_results=10):
        """Query and retrieve research outputs from Elasticsearch index."""
        query = {"bool": {"must": []}}
        if technique_id:
            query["bool"]["must"].append({"term": {"technique_id": technique_id}})
        if platform:
            query["bool"]["must"].append({"term": {"platform": platform}})
        if min_confidence:
            query["bool"]["must"].append({"range": {"confidence_score": {"gte": min_confidence}}})
        body = {"query": query, "size": max_results}
        res = self.es.search(index=self.output_index, body=body)
        return [hit["_source"] for hit in res["hits"]["hits"]]

    def refresh_feeds(self):
        """Refresh feeds to populate queue with new items when empty."""
        try:
            self.logger.info("Refreshing feeds to populate research queue...")
            # Import feed integrators with new paths
            import sys
            project_root = Path(__file__).parent.parent.parent.parent
            sys.path.insert(0, str(project_root))
            from feeds.integrators.mitre_attack import AutonomousFeedIntegrator
            from feeds.integrators.cve_integration import CVEFeedIntegrator
            
            # Run feed integrators with unified status manager
            feed_integrators = [
                AutonomousFeedIntegrator(status_path=str(self.status_manager.status_file)),
                CVEFeedIntegrator(status_path=str(self.status_manager.status_file)),
            ]
            
            for integrator in feed_integrators:
                try:
                    integrator.run()
                except Exception as e:
                    self.logger.error(f"Error running feed integrator: {e}")
            
            # Also process custom techniques during feed refresh
            try:
                self.process_custom_techniques()
                self.export_custom_techniques_to_elasticsearch()
                self.logger.info("Custom techniques processed and exported")
            except Exception as e:
                self.logger.error(f"Error processing custom techniques during refresh: {e}")
                    
            self.logger.info("Feed refresh completed")
        except Exception as e:
            self.logger.error(f"Error during feed refresh: {e}")
