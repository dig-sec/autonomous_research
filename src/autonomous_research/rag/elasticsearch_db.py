"""
Elasticsearch-based Vector Database for Enhanced        host: str = "localhost",
        port: int = 9200,
        user: str = "elastic",
        password: str = "",  # Should be set via environment variable
        index_name: str = "autonomous_research_rag",System

Implements Elasticsearch as the vector database backend with:
- Dense vector search using Elasticsearch
- Hybrid search (vector + text)
- Advanced filtering and aggregations
- Production-ready scalability
"""

import json
import time
import hashlib
from typing import Dict, List, Optional, Tuple, Any, Union
from pathlib import Path
import logging
from dataclasses import dataclass, asdict


try:
    from elasticsearch import Elasticsearch
    from elasticsearch.helpers import bulk
    ELASTICSEARCH_AVAILABLE = True
except ImportError:
    ELASTICSEARCH_AVAILABLE = False
    Elasticsearch = None
    bulk = None
    print("❌ Elasticsearch not available. Install with: pip install elasticsearch")

import sys
import os
from pathlib import Path

# Add src to path for testing
if __name__ == "__main__":
    current_dir = Path(__file__).parent
    src_dir = current_dir.parent.parent
    sys.path.insert(0, str(src_dir))

import numpy as np

from autonomous_research.rag.core import (
    DocumentChunk, Document, RetrievalResult, 
    EnhancedEmbeddingManager, DocumentProcessor
)
from autonomous_research.config.secure_config import get_elasticsearch_config


class ElasticsearchVectorDatabase:
    """
    Elasticsearch-based vector database with hybrid search capabilities.
    """
    
    def __init__(
        self,
        embedding_manager: EnhancedEmbeddingManager,
        host: str = "localhost",
        port: int = 9200,
        username: str = "elastic",
        password: str = "",  # Should be set via environment variable
        index_name: str = "autonomous_research_rag",
        similarity_threshold: float = 0.7,
        use_https: bool = False
    ):
        """
        Initialize Elasticsearch vector database.
        
        Args:
            embedding_manager: Embedding manager instance
            host: Elasticsearch host
            port: Elasticsearch port
            username: Elasticsearch username
            password: Elasticsearch password
            index_name: Name of the Elasticsearch index
            similarity_threshold: Minimum similarity for retrieval
            use_https: Whether to use HTTPS
        """
        self.embedding_manager = embedding_manager
        self.index_name = index_name
        self.similarity_threshold = similarity_threshold
        
        # Load Elasticsearch config
        es_config = get_elasticsearch_config()
        if not password:
            password = es_config.get('password', '')
        if host == "localhost":
            host = es_config.get('host', 'localhost')
        if port == 9200:
            port = es_config.get('port', 9200)
        if username == "elastic":
            username = es_config.get('user', 'elastic')
        
        if not ELASTICSEARCH_AVAILABLE:
            print("❌ Elasticsearch client not available")
            self.es = None
            return
        
        # Initialize Elasticsearch client
        if not ELASTICSEARCH_AVAILABLE:
            raise ImportError("Elasticsearch is not available. Please install the elasticsearch package.")
        self.es = Elasticsearch(
            [{"host": host, "port": port, "scheme": "https" if use_https else "http"}],
            basic_auth=(username, password),
            verify_certs=False,
            ssl_show_warn=False,
            request_timeout=30,
            retry_on_timeout=True,
            max_retries=3
        )
        
        # Test connection
        try:
            if self.es.ping():
                print(f"✅ Connected to Elasticsearch at {host}:{port}")
                self.setup_index()
            else:
                print(f"❌ Failed to connect to Elasticsearch at {host}:{port}")
                self.es = None
        except Exception as e:
            print(f"❌ Elasticsearch connection error: {e}")
            self.es = None
    
    def setup_index(self):
        """Set up the Elasticsearch index with proper mappings."""
        
        if not self.es:
            return
        
        # Define index mapping
        mapping = {
            "mappings": {
                "properties": {
                    "chunk_id": {"type": "keyword"},
                    "content": {
                        "type": "text",
                        "analyzer": "standard",
                        "fields": {
                            "keyword": {"type": "keyword", "ignore_above": 256}
                        }
                    },
                    "content_vector": {
                        "type": "dense_vector",
                        "dims": self.embedding_manager.embedding_dim,
                        "index": True,
                        "similarity": "cosine"
                    },
                    "source": {"type": "keyword"},
                    "document_id": {"type": "keyword"},
                    "document_title": {"type": "text"},
                    "chunk_index": {"type": "integer"},
                    "created_at": {"type": "date"},
                    "source_type": {"type": "keyword"},
                    "authority_score": {"type": "float"},
                    "mitre_techniques": {"type": "keyword"},
                    "security_frameworks": {"type": "keyword"},
                    "cves": {"type": "keyword"},
                    "word_count": {"type": "integer"},
                    "character_count": {"type": "integer"},
                    "chunk_size": {"type": "integer"},
                    "position_in_document": {"type": "float"},
                    "metadata": {"type": "object", "enabled": False}  # Store as blob
                }
            },
            "settings": {
                "number_of_shards": 1,
                "number_of_replicas": 0,  # Adjust for production
                "analysis": {
                    "analyzer": {
                        "security_analyzer": {
                            "type": "custom",
                            "tokenizer": "standard",
                            "filter": ["lowercase", "stop"]
                        }
                    }
                }
            }
        }
        
        try:
            # Create index if it doesn't exist
            if not self.es.indices.exists(index=self.index_name):
                self.es.indices.create(index=self.index_name, body=mapping)
                print(f"✅ Created Elasticsearch index: {self.index_name}")
            else:
                print(f"📁 Using existing Elasticsearch index: {self.index_name}")
                
            # Update mapping if needed (for existing index)
            try:
                self.es.indices.put_mapping(
                    index=self.index_name,
                    body=mapping["mappings"]
                )
            except Exception as e:
                # Mapping conflicts are expected for existing indices
                pass
                
        except Exception as e:
            print(f"❌ Failed to setup Elasticsearch index: {e}")
    
    def add_document(self, document: Document, chunk_processor: DocumentProcessor) -> int:
        """
        Add a document to the Elasticsearch index.
        
        Args:
            document: Document to add
            chunk_processor: Processor to create chunks
            
        Returns:
            Number of chunks added
        """
        if not self.es:
            print("❌ Elasticsearch not available")
            return 0
        
        # Create and process chunks
        chunks = chunk_processor.create_chunks(document)
        
        if not chunks:
            print(f"⚠️  No chunks created for document {document.title}")
            return 0
        
        # Generate embeddings for all chunks
        chunk_texts = [chunk.content for chunk in chunks]
        embeddings = self.embedding_manager.embed_batch(chunk_texts)
        
        # Prepare documents for bulk indexing
        docs_to_index = []
        
        for chunk, embedding in zip(chunks, embeddings):
            # Convert numpy array to list for JSON serialization
            embedding_list = embedding.tolist() if isinstance(embedding, np.ndarray) else embedding
            
            doc_body = {
                "chunk_id": chunk.id,
                "content": chunk.content,
                "content_vector": embedding_list,
                "source": chunk.source,
                "document_id": chunk.document_id,
                "document_title": document.title,
                "chunk_index": chunk.chunk_index,
                "created_at": time.time() * 1000,  # Elasticsearch expects milliseconds
                "source_type": document.source_type,
                "authority_score": document.authority_score,
                "mitre_techniques": chunk.metadata.get('mitre_techniques', []),
                "security_frameworks": chunk.metadata.get('security_frameworks', []),
                "cves": chunk.metadata.get('cves', []),
                "word_count": chunk.metadata.get('chunk_words', 0),
                "character_count": len(chunk.content),
                "chunk_size": chunk.metadata.get('chunk_size', 0),
                "position_in_document": chunk.metadata.get('position_in_document', 0.0),
                "metadata": chunk.metadata  # Store full metadata as object
            }
            
            docs_to_index.append({
                "_index": self.index_name,
                "_id": chunk.id,
                "_source": doc_body
            })
        
        # Bulk index the documents
        try:
            if not ELASTICSEARCH_AVAILABLE:
                raise ImportError("Elasticsearch bulk helper is not available.")
            success_count, errors = bulk(self.es, docs_to_index)
            
            if errors:
                if isinstance(errors, list):
                    print(f"⚠️  Some indexing errors occurred: {len(errors)} errors")
                    for error in errors[:3]:  # Show first 3 errors
                        print(f"   Error: {error}")
                else:
                    print(f"⚠️  Some indexing errors occurred: {errors} errors")
            
            # Refresh index to make documents immediately searchable
            self.es.indices.refresh(index=self.index_name)
            
            print(f"✅ Added document '{document.title}' with {success_count} chunks")
            return success_count
            
        except Exception as e:
            print(f"❌ Failed to index document {document.title}: {e}")
            return 0
    
    def search_similar_chunks(
        self,
        query: str,
        top_k: int = 10,
        similarity_threshold: Optional[float] = None,
        filter_metadata: Optional[Dict[str, Any]] = None,
        use_hybrid_search: bool = True
    ) -> List[RetrievalResult]:
        """
        Search for similar chunks using vector similarity and optional text search.
        
        Args:
            query: Search query
            top_k: Number of results to return
            similarity_threshold: Override default similarity threshold
            filter_metadata: Metadata filters to apply
            use_hybrid_search: Whether to combine vector and text search
            
        Returns:
            List of retrieval results
        """
        if not self.es:
            print("❌ Elasticsearch not available")
            return []
        
        if similarity_threshold is None:
            similarity_threshold = self.similarity_threshold
        
        # Generate query embedding
        query_embedding = self.embedding_manager.embed_text(query)
        query_vector = query_embedding.tolist() if isinstance(query_embedding, np.ndarray) else query_embedding
        
        # Build Elasticsearch query
        search_query = {
            "size": top_k * 2,  # Get more results for filtering
            "query": {
                "bool": {
                    "should": []
                }
            },
            "_source": {
                "excludes": ["content_vector"]  # Don't return the large vector in results
            }
        }
        
        # Vector similarity query
        vector_query = {
            "script_score": {
                "query": {"match_all": {}},
                "script": {
                    "source": "cosineSimilarity(params.query_vector, 'content_vector') + 1.0",
                    "params": {"query_vector": query_vector}
                },
                "min_score": similarity_threshold + 1.0  # Adjust for script_score offset
            }
        }
        search_query["query"]["bool"]["should"].append(vector_query)
        
        # Text search query (if hybrid search enabled)
        if use_hybrid_search:
            text_query = {
                "multi_match": {
                    "query": query,
                    "fields": ["content^2", "document_title"],
                    "type": "best_fields",
                    "boost": 0.3  # Lower weight than vector search
                }
            }
            search_query["query"]["bool"]["should"].append(text_query)
        
        # Add metadata filters
        if filter_metadata:
            filter_queries = []
            for key, value in filter_metadata.items():
                if isinstance(value, list):
                    filter_queries.append({"terms": {key: value}})
                else:
                    filter_queries.append({"term": {key: value}})
            
            if filter_queries:
                search_query["query"]["bool"]["filter"] = filter_queries
        
        # Add aggregations for analytics
        search_query["aggs"] = {
            "source_types": {"terms": {"field": "source_type"}},
            "frameworks": {"terms": {"field": "security_frameworks"}},
            "techniques": {"terms": {"field": "mitre_techniques"}}
        }
        
        try:
            # Execute search
            response = self.es.search(index=self.index_name, body=search_query)
            
            # Process results
            results = []
            for hit in response["hits"]["hits"]:
                source = hit["_source"]
                
                # Calculate similarity score (adjust from script_score)
                similarity_score = max(0.0, (hit["_score"] - 1.0))
                
                if similarity_score < similarity_threshold:
                    continue
                
                # Calculate authority and temporal scores
                authority_score = self._calculate_authority_score(source)
                temporal_score = self._calculate_temporal_score(source)
                
                # Combined score
                combined_score = (
                    similarity_score * 0.5 +
                    authority_score * 0.3 +
                    temporal_score * 0.2
                )
                
                # Create chunk object
                chunk = DocumentChunk(
                    id=source["chunk_id"],
                    content=source["content"],
                    source=source["source"],
                    document_id=source["document_id"],
                    chunk_index=source["chunk_index"],
                    metadata=source.get("metadata", {}),
                    created_at=source["created_at"] / 1000  # Convert back to seconds
                )
                
                result = RetrievalResult(
                    chunk=chunk,
                    similarity_score=similarity_score,
                    authority_score=authority_score,
                    temporal_score=temporal_score,
                    combined_score=combined_score,
                    rank=0  # Will be set after sorting
                )
                
                results.append(result)
            
            # Sort by combined score and assign ranks
            results.sort(key=lambda x: x.combined_score, reverse=True)
            for i, result in enumerate(results[:top_k]):
                result.rank = i + 1
            
            # Print search analytics
            self._print_search_analytics(response["aggregations"], len(results))
            
            return results[:top_k]
            
        except Exception as e:
            print(f"❌ Elasticsearch search error: {e}")
            return []
    
    def _calculate_authority_score(self, source: Dict) -> float:
        """Calculate authority score from Elasticsearch document source."""
        
        score = source.get("authority_score", 0.0)
        
        # Source type scoring
        source_type = source.get("source_type", "manual")
        source_scores = {
            'academic': 0.9,
            'github': 0.7,
            'cti': 0.8,
            'blog': 0.6,
            'manual': 0.5
        }
        score += source_scores.get(source_type, 0.5) * 0.4
        
        # Security framework mentions
        frameworks = source.get("security_frameworks", [])
        if 'MITRE_ATTACK' in frameworks:
            score += 0.3
        if any(fw in frameworks for fw in ['NIST', 'OWASP', 'CIS']):
            score += 0.2
        
        # MITRE technique mentions
        techniques = source.get("mitre_techniques", [])
        if techniques:
            score += min(0.2, len(techniques) * 0.05)
        
        # CVE mentions
        cves = source.get("cves", [])
        if cves:
            score += min(0.1, len(cves) * 0.02)
        
        return min(1.0, score)
    
    def _calculate_temporal_score(self, source: Dict) -> float:
        """Calculate temporal relevance score based on document age."""
        
        created_at = source.get("created_at", time.time() * 1000) / 1000  # Convert to seconds
        current_time = time.time()
        age_days = (current_time - created_at) / (24 * 3600)
        
        # Decay function: newer content scores higher
        if age_days <= 30:
            return 1.0
        elif age_days <= 90:
            return 0.8
        elif age_days <= 365:
            return 0.6
        elif age_days <= 730:
            return 0.4
        else:
            return 0.2
    
    def _print_search_analytics(self, aggregations: Dict, result_count: int):
        """Print search analytics from Elasticsearch aggregations."""
        
        print(f"📊 Search Analytics ({result_count} results):")
        
        # Source types
        source_types = aggregations.get("source_types", {}).get("buckets", [])
        if source_types:
            types_str = ", ".join([f"{bucket['key']}({bucket['doc_count']})" for bucket in source_types[:3]])
            print(f"   Source types: {types_str}")
        
        # Security frameworks
        frameworks = aggregations.get("frameworks", {}).get("buckets", [])
        if frameworks:
            frameworks_str = ", ".join([f"{bucket['key']}({bucket['doc_count']})" for bucket in frameworks[:3]])
            print(f"   Frameworks: {frameworks_str}")
        
        # MITRE techniques
        techniques = aggregations.get("techniques", {}).get("buckets", [])
        if techniques:
            techniques_str = ", ".join([f"{bucket['key']}({bucket['doc_count']})" for bucket in techniques[:3]])
            print(f"   Techniques: {techniques_str}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics from Elasticsearch."""
        
        if not self.es:
            return {"error": "Elasticsearch not available"}
        
        try:
            # Get index stats
            stats_response = self.es.indices.stats(index=self.index_name)
            index_stats = stats_response["indices"].get(self.index_name, {})
            
            # Get document count
            count_response = self.es.count(index=self.index_name)
            doc_count = count_response["count"]
            
            # Get unique document count
            unique_docs_query = {
                "aggs": {
                    "unique_documents": {
                        "cardinality": {"field": "document_id"}
                    },
                    "source_distribution": {
                        "terms": {"field": "source_type"}
                    }
                },
                "size": 0
            }
            
            agg_response = self.es.search(index=self.index_name, body=unique_docs_query)
            unique_docs = agg_response["aggregations"]["unique_documents"]["value"]
            source_distribution = {
                bucket["key"]: bucket["doc_count"] 
                for bucket in agg_response["aggregations"]["source_distribution"]["buckets"]
            }
            
            return {
                "total_chunks": doc_count,
                "total_documents": unique_docs,
                "index_size_bytes": index_stats.get("total", {}).get("store", {}).get("size_in_bytes", 0),
                "embedding_dimension": self.embedding_manager.embedding_dim,
                "elasticsearch_available": True,
                "source_type_distribution": source_distribution,
                "index_name": self.index_name
            }
            
        except Exception as e:
            return {"error": f"Failed to get statistics: {e}"}
    
    def delete_document(self, document_id: str) -> bool:
        """Delete all chunks for a document."""
        
        if not self.es:
            return False
        
        try:
            # Delete by query
            delete_query = {
                "query": {
                    "term": {"document_id": document_id}
                }
            }
            
            response = self.es.delete_by_query(index=self.index_name, body=delete_query)
            deleted_count = response.get("deleted", 0)
            
            print(f"✅ Deleted {deleted_count} chunks for document {document_id}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to delete document {document_id}: {e}")
            return False
    
    def clear_index(self) -> bool:
        """Clear all documents from the index."""
        
        if not self.es:
            return False
        
        try:
            self.es.delete_by_query(
                index=self.index_name,
                body={"query": {"match_all": {}}}
            )
            print(f"✅ Cleared index {self.index_name}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to clear index: {e}")
            return False


def test_elasticsearch_database():
    """Test the Elasticsearch vector database functionality."""
    print("🧪 Testing Elasticsearch Vector Database")
    print("=" * 50)
    
    # Initialize components
    embedding_manager = EnhancedEmbeddingManager(
        model_name="all-MiniLM-L6-v2",
        cache_dir="./cache/test_embeddings"
    )
    
    processor = DocumentProcessor(chunk_size=512)
    
    # Initialize Elasticsearch database
    es_db = ElasticsearchVectorDatabase(
        embedding_manager=embedding_manager,
        host="localhost",
        port=9200,
        username="elastic",
        password="",  # Should be set via environment variable
        index_name="test_autonomous_research_rag"
    )
    
    if not es_db.es:
        print("❌ Cannot test - Elasticsearch not available")
        return None
    
    # Test document with MITRE content
    test_content = """
# MITRE ATT&CK T1003: OS Credential Dumping

## Overview
Adversaries may attempt to dump credentials to obtain account login and credential material, normally in the form of a hash or a clear text password, from the operating system and software. Credentials can then be used to perform Lateral Movement and access restricted information.

## Sub-techniques
- T1003.001: LSASS Memory
- T1003.002: Security Account Manager  
- T1003.003: NTDS
- T1003.004: LSA Secrets
- T1003.005: Cached Domain Credentials

## Detection Methods
Monitor for unexpected processes interacting with LSASS.exe. Tools like Mimikatz and ProcDump are commonly used.

## References
- https://attack.mitre.org/techniques/T1003/
- CVE-2021-34527
"""
    
    # Process and add document
    doc = processor.process_markdown(test_content, "T1003_credential_dumping.md")
    doc.source_type = 'academic'
    doc.authority_score = 0.9
    
    chunks_added = es_db.add_document(doc, processor)
    print(f"✅ Added test document with {chunks_added} chunks")
    
    # Test search
    test_queries = [
        "credential dumping techniques",
        "LSASS memory extraction",
        "Mimikatz detection methods",
        "T1003 sub-techniques"
    ]
    
    for query in test_queries:
        print(f"\n🔍 Searching: '{query}'")
        results = es_db.search_similar_chunks(query, top_k=3)
        
        for result in results:
            print(f"  #{result.rank}: Score {result.combined_score:.3f} "
                  f"(sim: {result.similarity_score:.3f}, auth: {result.authority_score:.3f}, temp: {result.temporal_score:.3f})")
            print(f"           {result.chunk.content[:100]}...")
    
    # Show statistics
    print(f"\n📊 Database Statistics:")
    stats = es_db.get_statistics()
    for key, value in stats.items():
        if key != "error":
            print(f"   {key}: {value}")
    
    return es_db


if __name__ == "__main__":
    test_elasticsearch_database()
