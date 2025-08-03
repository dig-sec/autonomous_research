
import pytest
import numpy as np
from autonomous_research.rag.core import DocumentProcessor

def test_chunking_basic():
    processor = DocumentProcessor(chunk_size=20)
    text = "Para1. Sentence1. Sentence2.\n\nPara2. Sentence3. Sentence4."
    chunks = processor.smart_chunk_text(text)
    assert isinstance(chunks, list)
    assert all(isinstance(c, str) for c in chunks)
    assert len(chunks) > 0

def test_metadata_extraction():
    processor = DocumentProcessor()
    text = "T1003 CVE-2020-1234 https://example.com MITRE ATT&CK"
    meta = processor.extract_metadata(text, "source.md")
    assert "mitre_techniques" in meta
    assert "CVE-2020-1234" in meta["cves"]
    assert "MITRE_ATTACK" in meta["security_frameworks"]
    assert "referenced_urls" in meta
