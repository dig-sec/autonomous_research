"""
Elasticsearch Queue Manager

Manages research queue and status using Elasticsearch for better state management,
persistence, and scalability.
"""

import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path
from elasticsearch import Elasticsearch
from elasticsearch.exceptions import NotFoundError, ConnectionError

from autonomous_research.config.secure_config import get_elasticsearch_config


class ElasticsearchQueueManager:
    """Manages research queue and status using Elasticsearch."""
    
    def __init__(self, queue_index: str = "autonomous_research_queue", 
                 status_index: str = "autonomous_research_status"):
        self.queue_index = queue_index
        self.status_index = status_index
        self.logger = self._setup_logging()
        
        # Initialize Elasticsearch connection
        self.es = self._init_elasticsearch()
        
        # Create indices if they don't exist
        self._create_indices()
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration."""
        return logging.getLogger('elasticsearch_queue')
    
    def _init_elasticsearch(self) -> Elasticsearch:
        """Initialize Elasticsearch connection."""
        try:
            es_config = get_elasticsearch_config()
            es = Elasticsearch(
                hosts=[{
                    "host": es_config["host"],
                    "port": es_config["port"],
                    "scheme": "http"
                }],
                basic_auth=(es_config["user"], es_config["password"]),
                request_timeout=30,
                max_retries=3,
                retry_on_timeout=True
            )
            
            # Test connection
            if es.ping():
                self.logger.info(f"✅ Connected to Elasticsearch at {es_config['host']}:{es_config['port']}")
                return es
            else:
                raise ConnectionError("Could not ping Elasticsearch")
                
        except Exception as e:
            self.logger.error(f"❌ Failed to connect to Elasticsearch: {e}")
            raise
    
    def _create_indices(self):
        """Create Elasticsearch indices with appropriate mappings."""
        # Queue index mapping
        queue_mapping = {
            "mappings": {
                "properties": {
                    "id": {"type": "keyword"},
                    "type": {"type": "keyword"},  # technique, cve, news_article, etc.
                    "status": {"type": "keyword"},  # pending, processing, completed, failed
                    "priority": {"type": "integer"},
                    "created_at": {"type": "date"},
                    "updated_at": {"type": "date"},
                    "processed_at": {"type": "date"},
                    "platform": {"type": "keyword"},
                    "source": {"type": "keyword"},
                    "title": {"type": "text"},
                    "description": {"type": "text"},
                    "data": {"type": "object", "enabled": False},  # Store original data
                    "metadata": {"type": "object"},
                    "retry_count": {"type": "integer"},
                    "error_message": {"type": "text"}
                }
            }
        }
        
        # Status index mapping for system status
        status_mapping = {
            "mappings": {
                "properties": {
                    "component": {"type": "keyword"},
                    "status": {"type": "keyword"},
                    "last_updated": {"type": "date"},
                    "statistics": {"type": "object"},
                    "metadata": {"type": "object"}
                }
            }
        }
        
        # Create indices if they don't exist
        try:
            if not self.es.indices.exists(index=self.queue_index):
                self.es.indices.create(index=self.queue_index, body=queue_mapping)
                self.logger.info(f"📋 Created queue index: {self.queue_index}")
            
            if not self.es.indices.exists(index=self.status_index):
                self.es.indices.create(index=self.status_index, body=status_mapping)
                self.logger.info(f"📊 Created status index: {self.status_index}")
                
        except Exception as e:
            self.logger.error(f"❌ Error creating indices: {e}")
            raise
    
    def add_to_queue(self, items: List[Dict], item_type: str = "technique", 
                     priority: int = 1, source: str = "unknown") -> int:
        """Add items to the research queue."""
        added_count = 0
        current_time = datetime.now()
        
        for item in items:
            try:
                # Generate unique ID based on item content
                item_id = item.get("id", item.get("technique_id", f"{item_type}_{hash(str(item))}"))
                
                # Check if item already exists
                if self._item_exists(item_id):
                    self.logger.debug(f"Item {item_id} already exists in queue, skipping")
                    continue
                
                doc = {
                    "id": item_id,
                    "type": item_type,
                    "status": "pending",
                    "priority": priority,
                    "created_at": current_time,
                    "updated_at": current_time,
                    "platform": item.get("platform", "unknown"),
                    "source": source,
                    "title": item.get("name", item.get("title", item_id)),
                    "description": item.get("description", ""),
                    "data": item,  # Store original item data
                    "metadata": {
                        "added_by": "queue_manager",
                        "original_source": source
                    },
                    "retry_count": 0
                }
                
                self.es.index(index=self.queue_index, id=item_id, body=doc)
                added_count += 1
                
            except Exception as e:
                self.logger.error(f"Error adding item to queue: {e}")
        
        self.logger.info(f"✅ Added {added_count} items to queue")
        return added_count
    
    def _item_exists(self, item_id: str) -> bool:
        """Check if an item already exists in the queue."""
        try:
            self.es.get(index=self.queue_index, id=item_id)
            return True
        except NotFoundError:
            return False
        except Exception as e:
            self.logger.error(f"Error checking item existence: {e}")
            return False
    
    def get_pending_items(self, item_type: Optional[str] = None, 
                         limit: int = 10, platform: Optional[str] = None) -> List[Dict]:
        """Get pending items from the queue."""
        query = {
            "bool": {
                "must": [
                    {"term": {"status": "pending"}}
                ]
            }
        }
        
        if item_type:
            query["bool"]["must"].append({"term": {"type": item_type}})
        
        if platform:
            query["bool"]["must"].append({"term": {"platform": platform}})
        
        body = {
            "query": query,
            "sort": [
                {"priority": {"order": "desc"}},
                {"created_at": {"order": "asc"}}
            ],
            "size": limit
        }
        
        try:
            response = self.es.search(index=self.queue_index, body=body)
            items = []
            
            for hit in response["hits"]["hits"]:
                item = hit["_source"]
                item["_queue_id"] = hit["_id"]
                items.append(item)
            
            return items
            
        except Exception as e:
            self.logger.error(f"Error getting pending items: {e}")
            return []
    
    def update_item_status(self, item_id: str, status: str, 
                          error_message: Optional[str] = None,
                          metadata: Optional[Dict] = None) -> bool:
        """Update the status of a queue item."""
        try:
            update_doc = {
                "status": status,
                "updated_at": datetime.now()
            }
            
            if status == "completed":
                update_doc["processed_at"] = datetime.now()
            elif status == "failed":
                if error_message:
                    update_doc["error_message"] = error_message
                # Increment retry count
                try:
                    current_doc = self.es.get(index=self.queue_index, id=item_id)
                    retry_count = current_doc["_source"].get("retry_count", 0)
                    update_doc["retry_count"] = retry_count + 1
                except:
                    update_doc["retry_count"] = 1
            
            if metadata:
                update_doc["metadata"] = metadata
            
            self.es.update(
                index=self.queue_index,
                id=item_id,
                body={"doc": update_doc}
            )
            
            self.logger.debug(f"Updated item {item_id} status to {status}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating item status: {e}")
            return False
    
    def get_queue_stats(self) -> Dict:
        """Get statistics about the current queue."""
        try:
            # Get counts by status
            status_agg = {
                "aggs": {
                    "status_counts": {
                        "terms": {"field": "status"}
                    },
                    "type_counts": {
                        "terms": {"field": "type"}
                    },
                    "platform_counts": {
                        "terms": {"field": "platform"}
                    }
                }
            }
            
            response = self.es.search(index=self.queue_index, body=status_agg, size=0)
            
            stats = {
                "total_items": response["hits"]["total"]["value"],
                "by_status": {},
                "by_type": {},
                "by_platform": {},
                "last_updated": datetime.now().isoformat()
            }
            
            # Process aggregations
            for bucket in response["aggregations"]["status_counts"]["buckets"]:
                stats["by_status"][bucket["key"]] = bucket["doc_count"]
            
            for bucket in response["aggregations"]["type_counts"]["buckets"]:
                stats["by_type"][bucket["key"]] = bucket["doc_count"]
            
            for bucket in response["aggregations"]["platform_counts"]["buckets"]:
                stats["by_platform"][bucket["key"]] = bucket["doc_count"]
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Error getting queue stats: {e}")
            return {"error": str(e)}
    
    def clear_queue(self, status: Optional[str] = None) -> int:
        """Clear items from the queue."""
        try:
            query = {"match_all": {}}
            
            if status:
                query = {"term": {"status": status}}
            
            response = self.es.delete_by_query(
                index=self.queue_index,
                body={"query": query}
            )
            
            deleted_count = response.get("deleted", 0)
            self.logger.info(f"🗑️ Cleared {deleted_count} items from queue")
            return deleted_count
            
        except Exception as e:
            self.logger.error(f"Error clearing queue: {e}")
            return 0
    
    def retry_failed_items(self, max_retries: int = 3) -> int:
        """Reset failed items back to pending if they haven't exceeded max retries."""
        try:
            query = {
                "bool": {
                    "must": [
                        {"term": {"status": "failed"}},
                        {"range": {"retry_count": {"lt": max_retries}}}
                    ]
                }
            }
            
            # Get failed items that can be retried
            response = self.es.search(
                index=self.queue_index,
                body={"query": query, "size": 100}
            )
            
            retry_count = 0
            for hit in response["hits"]["hits"]:
                item_id = hit["_id"]
                if self.update_item_status(item_id, "pending"):
                    retry_count += 1
            
            self.logger.info(f"🔄 Reset {retry_count} failed items to pending")
            return retry_count
            
        except Exception as e:
            self.logger.error(f"Error retrying failed items: {e}")
            return 0
    
    def update_system_status(self, component: str, status: str, 
                           statistics: Optional[Dict] = None,
                           metadata: Optional[Dict] = None):
        """Update system component status."""
        try:
            doc = {
                "component": component,
                "status": status,
                "last_updated": datetime.now(),
                "statistics": statistics or {},
                "metadata": metadata or {}
            }
            
            self.es.index(index=self.status_index, id=component, body=doc)
            self.logger.debug(f"Updated {component} status to {status}")
            
        except Exception as e:
            self.logger.error(f"Error updating system status: {e}")
    
    def get_system_status(self, component: Optional[str] = None) -> Dict:
        """Get system status information."""
        try:
            if component:
                response = self.es.get(index=self.status_index, id=component)
                return response["_source"]
            else:
                response = self.es.search(
                    index=self.status_index,
                    body={"query": {"match_all": {}}, "size": 100}
                )
                
                status = {}
                for hit in response["hits"]["hits"]:
                    status[hit["_id"]] = hit["_source"]
                
                return status
                
        except Exception as e:
            self.logger.error(f"Error getting system status: {e}")
            return {"error": str(e)}
    
    def export_queue(self, output_file: Optional[str] = None) -> str:
        """Export queue to JSON file."""
        try:
            response = self.es.search(
                index=self.queue_index,
                body={"query": {"match_all": {}}, "size": 10000}
            )
            
            items = []
            for hit in response["hits"]["hits"]:
                item = hit["_source"]
                item["_queue_id"] = hit["_id"]
                items.append(item)
            
            if not output_file:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_file = f"queue_export_{timestamp}.json"
            
            with open(output_file, 'w') as f:
                json.dump(items, f, indent=2, default=str)
            
            self.logger.info(f"📁 Exported {len(items)} queue items to {output_file}")
            return output_file
            
        except Exception as e:
            self.logger.error(f"Error exporting queue: {e}")
            raise
