"""
Enhanced Vector Database and Retrieval System

Implements FAISS-based vector database with advanced retrieval features:
- Hierarchical retrieval (section → document → corpus)
- Temporal relevance scoring
- Source authority weighting
- Multi-model integration
"""

import json
import time
import pickle
from typing import Dict, List, Optional, Tuple, Any, Union
from pathlib import Path
import logging
from dataclasses import dataclass, asdict

import numpy as np
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import faiss

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False

from .core import (
    DocumentChunk, Document, RetrievalResult, 
    EnhancedEmbeddingManager, DocumentProcessor
)


class EnhancedVectorDatabase:
    """
    Advanced vector database with FAISS backend and enhanced retrieval features.
    """
    
    def __init__(
        self,
        embedding_manager: EnhancedEmbeddingManager,
        index_file: str = "./cache/vector_index.faiss",
        metadata_file: str = "./cache/vector_metadata.json",
        similarity_threshold: float = 0.7
    ):
        """
        Initialize enhanced vector database.
        
        Args:
            embedding_manager: Embedding manager instance
            index_file: Path to FAISS index file
            metadata_file: Path to metadata JSON file
            similarity_threshold: Minimum similarity for retrieval
        """
        self.embedding_manager = embedding_manager
        self.index_file = Path(index_file)
        self.metadata_file = Path(metadata_file)
        self.similarity_threshold = similarity_threshold
        
        # Create cache directories
        self.index_file.parent.mkdir(parents=True, exist_ok=True)
        self.metadata_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize FAISS index
        self.index = None
        self.chunk_metadata = {}  # Maps index position to chunk metadata
        self.document_registry = {}  # Maps document ID to document info
        self.next_index = 0
        
        self.initialize_index()
        self.load_existing_data()
        
        print(f"🗄️  Vector database initialized with {self.get_chunk_count()} chunks")
    
    def initialize_index(self):
        """Initialize FAISS index."""
        if not FAISS_AVAILABLE:
            print("❌ FAISS not available - vector search disabled")
            return
        
        embedding_dim = self.embedding_manager.embedding_dim
        
        # Use HNSW index for better performance with medium-sized datasets
        # For larger datasets, consider IVF indices
        if FAISS_AVAILABLE:
            self.index = faiss.IndexHNSWFlat(embedding_dim, 32)
            self.index.hnsw.efConstruction = 200
            self.index.hnsw.efSearch = 50
            print(f"✅ FAISS HNSW index initialized (dim: {embedding_dim})")
        else:
            print("⚠️  Using fallback similarity search")
    
    def load_existing_data(self):
        """Load existing index and metadata from disk."""
        try:
            # Load FAISS index
            if self.index_file.exists() and FAISS_AVAILABLE:
                self.index = faiss.read_index(str(self.index_file))
                print(f"📁 Loaded FAISS index with {self.index.ntotal} vectors")
            
            # Load metadata
            if self.metadata_file.exists():
                with open(self.metadata_file, 'r') as f:
                    data = json.load(f)
                    self.chunk_metadata = data.get('chunk_metadata', {})
                    self.document_registry = data.get('document_registry', {})
                    self.next_index = data.get('next_index', 0)
                print(f"📁 Loaded metadata for {len(self.chunk_metadata)} chunks")
        
        except Exception as e:
            print(f"⚠️  Failed to load existing data: {e}")
            self.chunk_metadata = {}
            self.document_registry = {}
            self.next_index = 0
    
    def save_data(self):
        """Save index and metadata to disk."""
        try:
            # Save FAISS index
            if self.index is not None and FAISS_AVAILABLE:
                faiss.write_index(self.index, str(self.index_file))
            
            # Save metadata
            metadata_dict = {
                'chunk_metadata': self.chunk_metadata,
                'document_registry': self.document_registry,
                'next_index': self.next_index,
                'saved_at': time.time()
            }
            
            with open(self.metadata_file, 'w') as f:
                json.dump(metadata_dict, f, indent=2, default=str)
            
            print(f"💾 Saved vector database with {len(self.chunk_metadata)} chunks")
        
        except Exception as e:
            print(f"❌ Failed to save vector database: {e}")
    
    def add_document(self, document: Document, chunk_processor: DocumentProcessor) -> int:
        """
        Add a document to the vector database.
        
        Args:
            document: Document to add
            chunk_processor: Processor to create chunks
            
        Returns:
            Number of chunks added
        """
        # Register document
        self.document_registry[document.id] = {
            'title': document.title,
            'source': document.source,
            'source_type': document.source_type,
            'authority_score': document.authority_score,
            'created_at': document.created_at,
            'last_updated': document.last_updated,
            'metadata': document.metadata
        }
        
        # Create and process chunks
        chunks = chunk_processor.create_chunks(document)
        
        if not chunks:
            print(f"⚠️  No chunks created for document {document.title}")
            return 0
        
        # Generate embeddings for all chunks
        chunk_texts = [chunk.content for chunk in chunks]
        embeddings = self.embedding_manager.embed_batch(chunk_texts)
        
        # Add to vector index
        chunk_count = 0
        for chunk, embedding in zip(chunks, embeddings):
            if self.add_chunk_to_index(chunk, embedding):
                chunk_count += 1
        
        print(f"✅ Added document '{document.title}' with {chunk_count} chunks")
        return chunk_count
    
    def add_chunk_to_index(self, chunk: DocumentChunk, embedding: np.ndarray) -> bool:
        """
        Add a single chunk to the vector index.
        
        Args:
            chunk: Document chunk to add
            embedding: Embedding vector for the chunk
            
        Returns:
            True if successfully added
        """
        try:
            # Store chunk metadata
            self.chunk_metadata[str(self.next_index)] = {
                'chunk_id': chunk.id,
                'content': chunk.content,
                'source': chunk.source,
                'document_id': chunk.document_id,
                'chunk_index': chunk.chunk_index,
                'metadata': chunk.metadata,
                'created_at': chunk.created_at,
                'index_position': self.next_index
            }
            
            # Add to FAISS index
            if self.index is not None and FAISS_AVAILABLE:
                embedding_2d = embedding.reshape(1, -1)
                self.index.add(embedding_2d)
            
            self.next_index += 1
            return True
        
        except Exception as e:
            print(f"❌ Failed to add chunk {chunk.id}: {e}")
            return False
    
    def search_similar_chunks(
        self,
        query: str,
        top_k: int = 10,
        similarity_threshold: Optional[float] = None,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[RetrievalResult]:
        """
        Search for similar chunks using vector similarity.
        
        Args:
            query: Search query
            top_k: Number of results to return
            similarity_threshold: Override default similarity threshold
            filter_metadata: Metadata filters to apply
            
        Returns:
            List of retrieval results
        """
        if similarity_threshold is None:
            similarity_threshold = self.similarity_threshold
        
        # Generate query embedding
        query_embedding = self.embedding_manager.embed_text(query)
        
        if self.index is None or not FAISS_AVAILABLE:
            return self._fallback_search(query, top_k, filter_metadata)
        
        # Search FAISS index
        query_2d = query_embedding.reshape(1, -1)
        scores, indices = self.index.search(query_2d, min(top_k * 2, self.index.ntotal))
        
        # Process results
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1:  # FAISS returns -1 for invalid indices
                continue
            
            # Convert FAISS distance to similarity (cosine similarity)
            similarity_score = 1.0 - (score / 2.0)  # Normalize L2 distance
            
            if similarity_score < similarity_threshold:
                continue
            
            # Get chunk metadata
            chunk_metadata = self.chunk_metadata.get(str(idx))
            if not chunk_metadata:
                continue
            
            # Apply metadata filters
            if filter_metadata and not self._matches_filter(chunk_metadata, filter_metadata):
                continue
            
            # Calculate authority and temporal scores
            authority_score = self._calculate_authority_score(chunk_metadata)
            temporal_score = self._calculate_temporal_score(chunk_metadata)
            
            # Combined score
            combined_score = (
                similarity_score * 0.5 +
                authority_score * 0.3 +
                temporal_score * 0.2
            )
            
            # Create retrieval result
            chunk = DocumentChunk(
                id=chunk_metadata['chunk_id'],
                content=chunk_metadata['content'],
                source=chunk_metadata['source'],
                document_id=chunk_metadata['document_id'],
                chunk_index=chunk_metadata['chunk_index'],
                metadata=chunk_metadata['metadata'],
                created_at=chunk_metadata['created_at']
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
        
        return results[:top_k]
    
    def _fallback_search(
        self,
        query: str,
        top_k: int,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[RetrievalResult]:
        """Fallback search using simple text matching when FAISS is not available."""
        
        query_lower = query.lower()
        results = []
        
        for idx_str, chunk_metadata in self.chunk_metadata.items():
            content = chunk_metadata['content'].lower()
            
            # Simple similarity based on word overlap
            query_words = set(query_lower.split())
            content_words = set(content.split())
            
            if len(query_words) == 0:
                continue
            
            similarity_score = len(query_words.intersection(content_words)) / len(query_words)
            
            if similarity_score < 0.1:  # Very low threshold for fallback
                continue
            
            # Apply metadata filters
            if filter_metadata and not self._matches_filter(chunk_metadata, filter_metadata):
                continue
            
            # Calculate scores
            authority_score = self._calculate_authority_score(chunk_metadata)
            temporal_score = self._calculate_temporal_score(chunk_metadata)
            combined_score = similarity_score * 0.6 + authority_score * 0.3 + temporal_score * 0.1
            
            # Create result
            chunk = DocumentChunk(
                id=chunk_metadata['chunk_id'],
                content=chunk_metadata['content'],
                source=chunk_metadata['source'],
                document_id=chunk_metadata['document_id'],
                chunk_index=chunk_metadata['chunk_index'],
                metadata=chunk_metadata['metadata'],
                created_at=chunk_metadata['created_at']
            )
            
            result = RetrievalResult(
                chunk=chunk,
                similarity_score=similarity_score,
                authority_score=authority_score,
                temporal_score=temporal_score,
                combined_score=combined_score,
                rank=0
            )
            
            results.append(result)
        
        # Sort and rank
        results.sort(key=lambda x: x.combined_score, reverse=True)
        for i, result in enumerate(results[:top_k]):
            result.rank = i + 1
        
        return results[:top_k]
    
    def _matches_filter(self, chunk_metadata: Dict, filter_metadata: Dict[str, Any]) -> bool:
        """Check if chunk metadata matches filter criteria."""
        
        for key, expected_value in filter_metadata.items():
            # Navigate nested metadata
            current = chunk_metadata
            for part in key.split('.'):
                if isinstance(current, dict) and part in current:
                    current = current[part]
                else:
                    return False
            
            # Check match
            if isinstance(expected_value, list):
                if current not in expected_value:
                    return False
            elif current != expected_value:
                return False
        
        return True
    
    def _calculate_authority_score(self, chunk_metadata: Dict) -> float:
        """Calculate authority score for a chunk based on source and metadata."""
        
        score = 0.0
        metadata = chunk_metadata.get('metadata', {})
        
        # Source type scoring
        source_type = metadata.get('document_source_type', 'manual')
        source_scores = {
            'academic': 0.9,
            'github': 0.7,
            'cti': 0.8,
            'blog': 0.6,
            'manual': 0.5
        }
        score += source_scores.get(source_type, 0.5) * 0.4
        
        # Security framework mentions
        frameworks = metadata.get('security_frameworks', [])
        if 'MITRE_ATTACK' in frameworks:
            score += 0.3
        if any(fw in frameworks for fw in ['NIST', 'OWASP', 'CIS']):
            score += 0.2
        
        # MITRE technique mentions
        techniques = metadata.get('mitre_techniques', [])
        if techniques:
            score += min(0.2, len(techniques) * 0.05)
        
        # CVE mentions
        cves = metadata.get('cves', [])
        if cves:
            score += min(0.1, len(cves) * 0.02)
        
        return min(1.0, score)
    
    def _calculate_temporal_score(self, chunk_metadata: Dict) -> float:
        """Calculate temporal relevance score based on document age."""
        
        created_at = chunk_metadata.get('created_at', time.time())
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
    
    def get_chunk_count(self) -> int:
        """Get total number of chunks in the database."""
        return len(self.chunk_metadata)
    
    def get_document_count(self) -> int:
        """Get total number of documents in the database."""
        return len(self.document_registry)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics."""
        
        stats = {
            'total_chunks': self.get_chunk_count(),
            'total_documents': self.get_document_count(),
            'index_size': self.index.ntotal if self.index and FAISS_AVAILABLE else 0,
            'embedding_dimension': self.embedding_manager.embedding_dim,
            'faiss_available': FAISS_AVAILABLE
        }
        
        # Source type distribution
        source_types = {}
        for doc_info in self.document_registry.values():
            source_type = doc_info.get('source_type', 'unknown')
            source_types[source_type] = source_types.get(source_type, 0) + 1
        stats['source_type_distribution'] = source_types
        
        # Framework coverage
        framework_count = 0
        technique_count = 0
        for chunk_meta in self.chunk_metadata.values():
            metadata = chunk_meta.get('metadata', {})
            if metadata.get('security_frameworks'):
                framework_count += 1
            if metadata.get('mitre_techniques'):
                technique_count += 1
        
        stats['chunks_with_frameworks'] = framework_count
        stats['chunks_with_techniques'] = technique_count
        
        return stats


def test_vector_database():
    """Test the enhanced vector database functionality."""
    print("🧪 Testing Enhanced Vector Database")
    print("=" * 45)
    
    # Initialize components
    embedding_manager = EnhancedEmbeddingManager(
        model_name="all-MiniLM-L6-v2",
        cache_dir="./cache/test_embeddings"
    )
    
    processor = DocumentProcessor(chunk_size=512)
    
    vector_db = EnhancedVectorDatabase(
        embedding_manager=embedding_manager,
        index_file="./cache/test_vector_index.faiss",
        metadata_file="./cache/test_vector_metadata.json"
    )
    
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
    
    chunks_added = vector_db.add_document(doc, processor)
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
        results = vector_db.search_similar_chunks(query, top_k=3)
        
        for result in results:
            print(f"  #{result.rank}: Score {result.combined_score:.3f} "
                  f"(sim: {result.similarity_score:.3f}, auth: {result.authority_score:.3f}, temp: {result.temporal_score:.3f})")
            print(f"           {result.chunk.content[:100]}...")
    
    # Show statistics
    print(f"\n📊 Database Statistics:")
    stats = vector_db.get_statistics()
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    # Save database
    vector_db.save_data()
    
    return vector_db


if __name__ == "__main__":
    test_vector_database()
