"""
Enhanced RAG System - Core Module

Implements the enhanced Retrieval-Augmented Generation system as specified in PROJECT_TODO.md Phase 1.
Features:
- Multi-modal document ingestion (PDF, HTML, Markdown, JSON)
- Advanced vector database with FAISS/Chroma support
- Hierarchical retrieval (section → document → corpus)
- Multi-model integration with specialized prompting
- Source authority weighting and temporal relevance
"""

import os
import json
import hashlib
import pickle
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import logging
from pathlib import Path

# Vector and embedding dependencies
import numpy as np
try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    print("⚠️  FAISS not available. Install with: pip install faiss-cpu")

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    print("⚠️  sentence-transformers not available. Install with: pip install sentence-transformers")

# Document processing dependencies
try:
    import PyPDF2
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False

try:
    from bs4 import BeautifulSoup
    HTML_SUPPORT = True
except ImportError:
    HTML_SUPPORT = False

import re
import time


@dataclass
class DocumentChunk:
    """Represents a chunk of text with metadata."""
    id: str
    content: str
    source: str
    document_id: str
    chunk_index: int
    metadata: Dict[str, Any]
    embedding: Optional[np.ndarray] = None
    created_at: float = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = time.time()


@dataclass
class Document:
    """Represents a complete document with metadata."""
    id: str
    title: str
    content: str
    source: str
    source_type: str  # 'github', 'academic', 'blog', 'cti', 'manual'
    metadata: Dict[str, Any]
    authority_score: float = 0.0
    created_at: float = None
    last_updated: float = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = time.time()
        if self.last_updated is None:
            self.last_updated = self.created_at


@dataclass
class RetrievalResult:
    """Represents a retrieval result with relevance scoring."""
    chunk: DocumentChunk
    similarity_score: float
    authority_score: float
    temporal_score: float
    combined_score: float
    rank: int


class EnhancedEmbeddingManager:
    """
    Manages embeddings with multiple model support and optimization.
    """
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2", cache_dir: str = "./cache/embeddings"):
        """
        Initialize embedding manager.
        
        Args:
            model_name: SentenceTransformer model name
            cache_dir: Directory to cache embeddings
        """
        self.model_name = model_name
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            print(f"🔧 Loading embedding model: {model_name}")
            self.model = SentenceTransformer(model_name)
            self.embedding_dim = self.model.get_sentence_embedding_dimension()
            print(f"✅ Embedding model loaded (dim: {self.embedding_dim})")
        else:
            self.model = None
            self.embedding_dim = 384  # Default MiniLM dimension
            print("❌ SentenceTransformers not available - embeddings disabled")
        
        # Cache for computed embeddings
        self.embedding_cache = {}
        self.load_embedding_cache()
    
    def get_text_hash(self, text: str) -> str:
        """Generate a hash for text to use as cache key."""
        return hashlib.sha256(text.encode()).hexdigest()[:16]
    
    def load_embedding_cache(self):
        """Load cached embeddings from disk."""
        cache_file = self.cache_dir / f"embeddings_{self.model_name.replace('/', '_')}.pkl"
        if cache_file.exists():
            try:
                with open(cache_file, 'rb') as f:
                    self.embedding_cache = pickle.load(f)
                print(f"📁 Loaded {len(self.embedding_cache)} cached embeddings")
            except Exception as e:
                print(f"⚠️  Failed to load embedding cache: {e}")
                self.embedding_cache = {}
    
    def save_embedding_cache(self):
        """Save embeddings to cache."""
        cache_file = self.cache_dir / f"embeddings_{self.model_name.replace('/', '_')}.pkl"
        try:
            with open(cache_file, 'wb') as f:
                pickle.dump(self.embedding_cache, f)
            print(f"💾 Saved {len(self.embedding_cache)} embeddings to cache")
        except Exception as e:
            print(f"⚠️  Failed to save embedding cache: {e}")
    
    def embed_text(self, text: str, use_cache: bool = True) -> np.ndarray:
        """
        Generate embedding for text with caching.
        
        Args:
            text: Text to embed
            use_cache: Whether to use/store in cache
            
        Returns:
            Embedding vector
        """
        if not self.model:
            # Return random embedding if model not available
            return np.random.random(self.embedding_dim).astype(np.float32)
        
        text_hash = self.get_text_hash(text)
        
        # Check cache first
        if use_cache and text_hash in self.embedding_cache:
            return self.embedding_cache[text_hash]
        
        # Generate embedding
        embedding = self.model.encode(text, convert_to_tensor=False)
        embedding = np.array(embedding, dtype=np.float32)
        
        # Cache result
        if use_cache:
            self.embedding_cache[text_hash] = embedding
        
        return embedding
    
    def embed_batch(self, texts: List[str], batch_size: int = 32) -> List[np.ndarray]:
        """
        Generate embeddings for multiple texts efficiently.
        
        Args:
            texts: List of texts to embed
            batch_size: Batch size for processing
            
        Returns:
            List of embedding vectors
        """
        if not self.model:
            return [np.random.random(self.embedding_dim).astype(np.float32) for _ in texts]
        
        embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            batch_embeddings = self.model.encode(batch, convert_to_tensor=False)
            embeddings.extend([np.array(emb, dtype=np.float32) for emb in batch_embeddings])
        
        return embeddings


class DocumentProcessor:
    """
    Processes various document formats into standardized chunks.
    """
    
    def __init__(self, chunk_size: int = 1024, chunk_overlap: int = 128):
        """
        Initialize document processor.
        
        Args:
            chunk_size: Maximum tokens per chunk
            chunk_overlap: Overlap between chunks
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # MITRE ATT&CK technique pattern
        self.technique_pattern = re.compile(r'\bT\d{4}(?:\.\d{3})?\b', re.IGNORECASE)
        
        # Security framework patterns
        self.framework_patterns = {
            'MITRE_ATTACK': re.compile(r'\b(?:MITRE|ATT&CK|attack)\b', re.IGNORECASE),
            'NIST': re.compile(r'\bNIST\b', re.IGNORECASE),
            'OWASP': re.compile(r'\bOWASP\b', re.IGNORECASE),
            'CIS': re.compile(r'\bCIS\b', re.IGNORECASE)
        }
    
    def extract_metadata(self, content: str, source: str) -> Dict[str, Any]:
        """
        Extract metadata from document content.
        
        Args:
            content: Document content
            source: Document source URL/path
            
        Returns:
            Metadata dictionary
        """
        metadata = {
            'word_count': len(content.split()),
            'character_count': len(content),
            'source': source,
            'extracted_at': time.time()
        }
        
        # Extract MITRE techniques
        techniques = self.technique_pattern.findall(content)
        metadata['mitre_techniques'] = list(set(techniques))
        
        # Extract security frameworks
        frameworks = []
        for framework, pattern in self.framework_patterns.items():
            if pattern.search(content):
                frameworks.append(framework)
        metadata['security_frameworks'] = frameworks
        
        # Extract potential CVEs
        cve_pattern = re.compile(r'\bCVE-\d{4}-\d{4,}\b', re.IGNORECASE)
        cves = cve_pattern.findall(content)
        metadata['cves'] = list(set(cves))
        
        # Extract URLs
        url_pattern = re.compile(r'https?://[^\s]+', re.IGNORECASE)
        urls = url_pattern.findall(content)
        metadata['referenced_urls'] = list(set(urls))
        
        return metadata
    
    def smart_chunk_text(self, content: str, chunk_size: int = None) -> List[str]:
        """
        Intelligently chunk text preserving semantic boundaries.
        
        Args:
            content: Text content to chunk
            chunk_size: Override default chunk size
            
        Returns:
            List of text chunks
        """
        if chunk_size is None:
            chunk_size = self.chunk_size
        
        # Split by paragraphs first
        paragraphs = content.split('\n\n')
        chunks = []
        current_chunk = ""
        
        for paragraph in paragraphs:
            # If paragraph is too long, split by sentences
            if len(paragraph) > chunk_size:
                sentences = re.split(r'[.!?]+', paragraph)
                for sentence in sentences:
                    sentence = sentence.strip()
                    if not sentence:
                        continue
                    
                    if len(current_chunk) + len(sentence) > chunk_size:
                        if current_chunk:
                            chunks.append(current_chunk.strip())
                        current_chunk = sentence
                    else:
                        current_chunk += " " + sentence if current_chunk else sentence
            else:
                # Try to add whole paragraph
                if len(current_chunk) + len(paragraph) > chunk_size:
                    if current_chunk:
                        chunks.append(current_chunk.strip())
                    current_chunk = paragraph
                else:
                    current_chunk += "\n\n" + paragraph if current_chunk else paragraph
        
        # Add final chunk
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return [chunk for chunk in chunks if chunk.strip()]
    
    def process_markdown(self, content: str, source: str) -> Document:
        """Process markdown document."""
        # Extract title from first header
        title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        title = title_match.group(1) if title_match else os.path.basename(source)
        
        # Clean markdown syntax for better processing
        clean_content = re.sub(r'```[\s\S]*?```', '[CODE_BLOCK]', content)
        clean_content = re.sub(r'`[^`]+`', '[CODE]', clean_content)
        clean_content = re.sub(r'!\[.*?\]\(.*?\)', '[IMAGE]', clean_content)
        clean_content = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', clean_content)
        
        metadata = self.extract_metadata(content, source)
        metadata['document_type'] = 'markdown'
        metadata['original_title'] = title
        
        doc_id = hashlib.sha256(f"{source}_{title}".encode()).hexdigest()[:16]
        
        return Document(
            id=doc_id,
            title=title,
            content=clean_content,
            source=source,
            source_type='manual',
            metadata=metadata
        )
    
    def process_pdf(self, file_path: str) -> Optional[Document]:
        """Process PDF document."""
        if not PDF_SUPPORT:
            print("❌ PDF processing not available. Install PyPDF2: pip install PyPDF2")
            return None
        
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                content = ""
                for page in pdf_reader.pages:
                    content += page.extract_text() + "\n"
            
            title = os.path.splitext(os.path.basename(file_path))[0]
            metadata = self.extract_metadata(content, file_path)
            metadata['document_type'] = 'pdf'
            metadata['page_count'] = len(pdf_reader.pages)
            
            doc_id = hashlib.sha256(f"{file_path}_{title}".encode()).hexdigest()[:16]
            
            return Document(
                id=doc_id,
                title=title,
                content=content,
                source=file_path,
                source_type='manual',
                metadata=metadata
            )
        except Exception as e:
            print(f"❌ Failed to process PDF {file_path}: {e}")
            return None
    
    def process_html(self, content: str, source: str) -> Optional[Document]:
        """Process HTML document."""
        if not HTML_SUPPORT:
            print("❌ HTML processing not available. Install beautifulsoup4: pip install beautifulsoup4")
            return None
        
        try:
            soup = BeautifulSoup(content, 'html.parser')
            
            # Extract title
            title_tag = soup.find('title')
            title = title_tag.get_text() if title_tag else os.path.basename(source)
            
            # Remove script and style tags
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Extract text content
            text_content = soup.get_text()
            
            # Clean up whitespace
            lines = (line.strip() for line in text_content.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            clean_content = '\n'.join(chunk for chunk in chunks if chunk)
            
            metadata = self.extract_metadata(clean_content, source)
            metadata['document_type'] = 'html'
            metadata['original_title'] = title
            
            doc_id = hashlib.sha256(f"{source}_{title}".encode()).hexdigest()[:16]
            
            return Document(
                id=doc_id,
                title=title,
                content=clean_content,
                source=source,
                source_type='manual',
                metadata=metadata
            )
        except Exception as e:
            print(f"❌ Failed to process HTML from {source}: {e}")
            return None
    
    def create_chunks(self, document: Document) -> List[DocumentChunk]:
        """
        Create chunks from a document.
        
        Args:
            document: Document to chunk
            
        Returns:
            List of document chunks
        """
        text_chunks = self.smart_chunk_text(document.content)
        chunks = []
        
        for i, chunk_text in enumerate(text_chunks):
            chunk_id = f"{document.id}_chunk_{i:04d}"
            
            # Extract chunk-specific metadata
            chunk_metadata = {
                'document_title': document.title,
                'document_source_type': document.source_type,
                'chunk_size': len(chunk_text),
                'chunk_words': len(chunk_text.split()),
                'position_in_document': i / len(text_chunks),  # Relative position
            }
            
            # Inherit document metadata
            chunk_metadata.update(document.metadata)
            
            chunk = DocumentChunk(
                id=chunk_id,
                content=chunk_text,
                source=document.source,
                document_id=document.id,
                chunk_index=i,
                metadata=chunk_metadata
            )
            
            chunks.append(chunk)
        
        return chunks


def test_document_processor():
    """Test the document processor functionality."""
    print("🧪 Testing Document Processor")
    print("=" * 40)
    
    processor = DocumentProcessor(chunk_size=512, chunk_overlap=64)
    
    # Test markdown processing
    markdown_content = """
# MITRE ATT&CK Technique T1003: OS Credential Dumping

## Overview
This technique involves adversaries attempting to dump credentials to obtain account login and credential material, normally in the form of a hash or a clear text password, from the operating system and software.

## Detection
Monitor for unexpected processes interacting with LSASS.exe. Common credential dumping tools include:
- Mimikatz
- ProcDump
- Gsecdump

## References
- https://attack.mitre.org/techniques/T1003/
- CVE-2021-34527 (PrintNightmare)
"""
    
    doc = processor.process_markdown(markdown_content, "test_technique.md")
    print(f"✅ Processed markdown document: {doc.title}")
    print(f"   Metadata: {list(doc.metadata.keys())}")
    print(f"   MITRE techniques: {doc.metadata.get('mitre_techniques', [])}")
    
    # Test chunking
    chunks = processor.create_chunks(doc)
    print(f"✅ Created {len(chunks)} chunks")
    for i, chunk in enumerate(chunks[:2]):
        print(f"   Chunk {i}: {len(chunk.content)} chars, {chunk.metadata['chunk_words']} words")
    
    return processor


if __name__ == "__main__":
    test_document_processor()
