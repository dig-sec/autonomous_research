"""
Enhanced RAG System - Main Module

This module provides the main interface for the enhanced RAG system
implementing Phase 1 of the PROJECT_TODO.md requirements.

Now supports Elasticsearch as the primary vector database backend.
"""

from .core import (
    DocumentChunk,
    Document, 
    RetrievalResult,
    EnhancedEmbeddingManager,
    DocumentProcessor,
    test_document_processor
)

from .elasticsearch_db import (
    ElasticsearchVectorDatabase,
    test_elasticsearch_database
)

from .vector_db import (
    EnhancedVectorDatabase,
    test_vector_database
)

from .integration import (
    EnhancedRAGSystem,
    StandaloneElasticsearchRAG,
    ModelSpecificRAGPromptBuilder,
    ContextOptimizer,
    RAGContext,
    test_rag_integration
)

__all__ = [
    'DocumentChunk',
    'Document',
    'RetrievalResult', 
    'EnhancedEmbeddingManager',
    'DocumentProcessor',
    'ElasticsearchVectorDatabase',
    'EnhancedVectorDatabase',
    'EnhancedRAGSystem',
    'StandaloneElasticsearchRAG',
    'ModelSpecificRAGPromptBuilder',
    'ContextOptimizer',
    'RAGContext',
    'test_document_processor',
    'test_elasticsearch_database',
    'test_vector_database',
    'test_rag_integration'
]
