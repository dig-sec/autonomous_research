#!/usr/bin/env python3
"""
Example: Using the Enhanced RAG System with Elasticsearch

This script demonstrates how to use the new Elasticsearch-based RAG system
for autonomous research with your local Elasticsearch instance.

Prerequisites:
1. Elasticsearch running on localhost:9200
2. Dependencies installed: make setup (see Makefile)
"""

import sys
import os
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
src_path = project_root / "src"
if src_path.exists():
    sys.path.insert(0, str(src_path))

from autonomous_research.rag import StandaloneElasticsearchRAG


def main():
    print("🔬 Enhanced RAG System with Elasticsearch - Demo")
    print("=" * 50)
    
    # Initialize the RAG system with your Elasticsearch credentials
    print("🔧 Initializing Elasticsearch RAG system...")
    # Load secure configuration
    import sys
    sys.path.append('src')
    from autonomous_research.config.secure_config import get_elasticsearch_config
    es_config = get_elasticsearch_config()
    
    rag = StandaloneElasticsearchRAG(
        embedding_model="all-MiniLM-L6-v2",
        elasticsearch_host=es_config["host"],
        elasticsearch_port=es_config["port"],
        elasticsearch_user=es_config["user"],
        elasticsearch_password=es_config["password"],
        cache_dir="./cache/elasticsearch_rag"
    )
    
    if not rag.vector_db.es:
        print("❌ Failed to connect to Elasticsearch. Please ensure it's running on localhost:9200")
        print("   Start Elasticsearch and try again.")
        return
    
    print("✅ Connected to Elasticsearch successfully!")
    
    # Add some sample cybersecurity documents
    sample_documents = [
        {
            "title": "MITRE ATT&CK T1003 - OS Credential Dumping",
            "content": """
# T1003: OS Credential Dumping

## Overview
Adversaries may attempt to dump credentials to obtain account login and credential material, normally in the form of a hash or a clear text password, from the operating system and software.

## Sub-techniques
- T1003.001: LSASS Memory - Access LSASS memory to obtain credentials
- T1003.002: Security Account Manager - Extract from SAM database
- T1003.003: NTDS - Dump Active Directory database
- T1003.004: LSA Secrets - Extract LSA secrets
- T1003.005: Cached Domain Credentials - Extract cached credentials

## Detection
Monitor for unexpected processes interacting with LSASS.exe. Common tools:
- Mimikatz - Most common credential dumping tool
- ProcDump - Microsoft utility often abused
- Gsecdump - SAM and LSA extraction tool

## Mitigation
- Enable Credential Guard on Windows 10/11
- Restrict administrative privileges
- Monitor LSASS access
- Use Protected Process Light (PPL) for LSASS
""",
            "source": "mitre_attack_t1003.md",
            "source_type": "academic"
        },
        {
            "title": "Mimikatz Detection and Response Guide",
            "content": """
from src.autonomous_research.rag import StandaloneElasticsearchRAG
from src.autonomous_research.config.secure_config import get_elasticsearch_config

# Mimikatz Detection and Response

## What is Mimikatz?
Mimikatz is a powerful post-exploitation tool that can extract plaintext passwords, hash, PIN code and kerberos tickets from memory. It's commonly used by both attackers and security professionals.

## Detection Methods

### Process Monitoring
- Monitor for sekurlsa::logonpasswords command
- Watch for privilege::debug attempts
- Detect token::elevate usage

### Memory Analysis
- Look for LSASS memory dumps
- Monitor for unusual LSASS process access
- Check for memory pattern signatures

### Network Indicators
- Kerberos ticket extraction attempts
- Pass-the-hash lateral movement
- Golden ticket creation

## Response Actions
1. Isolate affected systems immediately
2. Force password resets for all users
3. Revoke and reissue Kerberos tickets
4. Analyze logs for lateral movement
5. Check for persistence mechanisms

## Prevention
- Implement Credential Guard
- Use LAPS for local admin passwords
- Enable PtH mitigations
- Regular security awareness training
""",
            "source": "mimikatz_detection_guide.md",
            "source_type": "manual"
        },
        {
            "title": "Windows Event Log Analysis for Credential Theft",
            "content": """
# Windows Event Log Analysis for Credential Theft Detection

## Key Event IDs to Monitor

### Security Events
- 4648: Logon with explicit credentials (possible pass-the-hash)
- 4624: Successful logon (monitor for unusual patterns)
- 4625: Failed logon (brute force attempts)
- 4672: Admin rights assigned (privilege escalation)

### System Events  
- 7045: Service installation (persistence mechanism)
- 7036: Service state changes (suspicious services)

### Application Events
- Monitor for PowerShell execution (event ID 4103, 4104)
- WMI events for lateral movement
- Scheduled task creation/modification

## Indicators of Credential Dumping

### LSASS Access Patterns
- Multiple processes accessing LSASS memory
- Non-standard tools reading LSASS
- Memory dumps of LSASS process

### Authentication Anomalies
- Logons from unusual locations
- Multiple failed attempts followed by success
- Service account logons from workstations

## Analysis Techniques
1. Correlate events across multiple systems
2. Look for time-based patterns
3. Analyze user behavior baselines
4. Cross-reference with threat intelligence

## Tools for Analysis
- Sysmon for enhanced logging
- Splunk/ELK for log aggregation
- Sigma rules for detection
- YARA rules for file analysis
""",
            "source": "windows_event_analysis.md", 
            "source_type": "manual"
        }
    ]
    
    # Add documents to the RAG system
    print("\n📚 Adding sample cybersecurity documents...")
    for doc in sample_documents:
        success = rag.add_document_from_text(
            content=doc["content"],
            title=doc["title"],
            source=doc["source"],
            source_type=doc["source_type"]
        )
        if success:
            print(f"   ✅ Added: {doc['title']}")
        else:
            print(f"   ❌ Failed: {doc['title']}")
    
    # Show statistics
    print("\n📊 RAG System Statistics:")
    stats = rag.get_statistics()
    for key, value in stats.items():
        if key != "error":
            print(f"   {key}: {value}")
    
    # Test search functionality
    test_queries = [
        "How does Mimikatz work?",
        "What are T1003 sub-techniques?", 
        "How to detect credential dumping?",
        "Windows event IDs for credential theft",
        "LSASS memory protection methods"
    ]
    
    print("\n🔍 Testing Search Functionality:")
    print("-" * 40)
    
    for query in test_queries:
        print(f"\n🔎 Query: '{query}'")
        results = rag.search(query, top_k=3)
        
        if results:
            for i, result in enumerate(results, 1):
                print(f"   #{i}: {result.chunk.source} (score: {result.combined_score:.3f})")
                print(f"        {result.chunk.content[:100]}...")
        else:
            print("   No results found")
    
    # Test context generation
    print("\n📝 Testing Context Generation:")
    print("-" * 40)
    
    context_query = "How to detect and respond to Mimikatz attacks?"
    print(f"\n🎯 Context Query: '{context_query}'")
    
    context = rag.get_context_for_query(context_query, max_length=1500)
    print("\n📋 Generated Context:")
    print("─" * 60)
    print(context)
    print("─" * 60)
    
    print("\n🎉 Demo completed successfully!")
    print("\n💡 Next steps:")
    print("   1. Add your own documents using rag.add_document_from_file()")
    print("   2. Integrate with your AI models for RAG-enhanced responses")
    print("   3. Customize search parameters and embedding models")
    print("   4. Scale up with additional Elasticsearch nodes")


if __name__ == "__main__":
    main()
