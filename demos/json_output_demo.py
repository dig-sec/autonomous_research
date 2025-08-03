#!/usr/bin/env python3
"""
JSON Output System Demo

Demonstrates the new JSON-based Elasticsearch output system
that replaces file-based markdown outputs.
"""

import asyncio
import json
from pathlib import Path
from typing import Dict, List

# Setup path for imports
import sys
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

import sys
import os
from pathlib import Path

# Add project paths
sys.path.insert(0, '/home/pabi/git/autonomous_research')
sys.path.insert(0, '/home/pabi/git/autonomous_research/src')

from autonomous_research.output.elasticsearch_output_manager import (
    ResearchOutput, ElasticsearchOutputManager, create_unified_research_output
)
from autonomous_research.generation.enhanced_content_generator import EnhancedContentGenerator
from autonomous_research.integration.json_output_migration import integrate_json_output_system


def demo_research_output_creation():
    """Demonstrate creating a research output object."""
    print("🎯 Demo 1: Creating Research Output Object")
    print("=" * 50)
    
    # Sample technique data
    technique = {
        "id": "T1055",
        "name": "Process Injection",
        "platform": "windows",
        "category": "defense_evasion"
    }
    
    # Sample content sections
    content_sections = {
        "description": """
Process injection is a technique used by adversaries to execute code in the address space of another process. 
This technique allows malware to hide its presence, evade detection, and gain access to system resources 
through legitimate processes. Common injection methods include DLL injection, process hollowing, and reflective loading.
        """.strip(),
        
        "detection": """
Key detection indicators include:
- Unusual network activity from system processes
- Processes with unexpected loaded modules
- Abnormal memory patterns and allocations
- Suspicious API calls (VirtualAllocEx, WriteProcessMemory, CreateRemoteThread)
- Process behavior inconsistent with expected functionality
        """.strip(),
        
        "mitigation": """
Mitigation strategies include:
- Enable application whitelisting and code signing verification
- Implement process monitoring and behavioral analysis
- Use endpoint detection and response (EDR) solutions
- Apply principle of least privilege
- Regular security updates and patch management
        """.strip(),
        
        "purple_playbook": """
Purple team exercise for process injection:
1. Red team: Implement process injection using common tools (Metasploit, Cobalt Strike)
2. Blue team: Monitor for injection indicators using SIEM and EDR
3. Validate detection rules and response procedures
4. Document lessons learned and improve defenses
        """.strip()
    }
    
    # Create research output
    research_output = create_unified_research_output(
        technique=technique,
        research_context="Comprehensive analysis of process injection techniques",
        content_sections=content_sections,
        sources=["MITRE ATT&CK", "Security Research Papers", "Incident Reports"],
        confidence_score=8.5
    )
    
    print(f"✅ Created research output:")
    print(f"   - Technique: {research_output.technique_id} - {research_output.technique_name}")
    print(f"   - Platform: {research_output.platform}")
    print(f"   - Quality Score: {research_output.quality_score:.2f}")
    print(f"   - Completeness: {research_output.completeness_score:.2f}")
    print(f"   - Word Count: {research_output.word_count}")
    print(f"   - Tags: {research_output.tags}")
    print()
    
    return research_output


def demo_elasticsearch_storage(research_output: ResearchOutput):
    """Demonstrate storing and retrieving from Elasticsearch."""
    print("🎯 Demo 2: Elasticsearch Storage & Retrieval")
    print("=" * 50)
    
    # Initialize output manager
    output_manager = ElasticsearchOutputManager()
    
    if not output_manager.es:
        print("❌ Elasticsearch not available - skipping storage demo")
        return
    
    # Store research output
    print("📤 Storing research output in Elasticsearch...")
    success = output_manager.store_research_output(research_output)
    
    if success:
        print("✅ Successfully stored research output")
        
        # Retrieve the output
        print("📥 Retrieving research output...")
        retrieved_output = output_manager.get_research_output(
            research_output.technique_id, 
            research_output.platform
        )
        
        if retrieved_output:
            print("✅ Successfully retrieved research output")
            print(f"   - Retrieved technique: {retrieved_output.technique_name}")
            print(f"   - Quality score: {retrieved_output.quality_score:.2f}")
            print(f"   - Content sections filled: {int(retrieved_output.completeness_score * 6)}/6")
        else:
            print("❌ Failed to retrieve research output")
            
        # Search for outputs
        print("\n🔍 Searching for process injection related outputs...")
        search_results = output_manager.search_research_outputs(
            query="process injection",
            platform="windows",
            limit=5
        )
        
        print(f"✅ Found {len(search_results)} matching outputs")
        for output in search_results:
            print(f"   - {output.technique_id}: {output.technique_name} (Quality: {output.quality_score:.2f})")
            
    else:
        print("❌ Failed to store research output")
    
    print()


def demo_analytics_dashboard():
    """Demonstrate analytics capabilities."""
    print("🎯 Demo 3: Analytics Dashboard")
    print("=" * 50)
    
    output_manager = ElasticsearchOutputManager()
    
    if not output_manager.es:
        print("❌ Elasticsearch not available - skipping analytics demo")
        return
    
    # Get analytics summary
    analytics = output_manager.get_analytics_summary()
    
    print("📊 Research Output Analytics:")
    print(f"   - Total Outputs: {analytics.get('total_outputs', 0)}")
    print(f"   - Average Quality Score: {analytics.get('avg_quality_score', 0):.2f}")
    print(f"   - Average Completeness: {analytics.get('avg_completeness_score', 0):.2f}")
    print(f"   - Complete Outputs: {analytics.get('complete_outputs', 0)}")
    print(f"   - High Quality Outputs: {analytics.get('high_quality_outputs', 0)}")
    print(f"   - Outputs with Detection: {analytics.get('outputs_with_detection', 0)}")
    print(f"   - Outputs with Mitigation: {analytics.get('outputs_with_mitigation', 0)}")
    print(f"   - Total Word Count: {analytics.get('total_word_count', 0):,}")
    
    print("\n📈 Platform Distribution:")
    platforms = analytics.get('platforms', {})
    for platform, count in platforms.items():
        print(f"   - {platform}: {count}")
    
    print("\n📈 Category Distribution:")
    categories = analytics.get('categories', {})
    for category, count in categories.items():
        print(f"   - {category}: {count}")
    
    print()


def demo_content_generation():
    """Demonstrate enhanced content generation."""
    print("🎯 Demo 4: Enhanced Content Generation")
    print("=" * 50)
    
    # Initialize enhanced content generator
    generator = EnhancedContentGenerator()
    
    # Sample technique for generation
    technique = {
        "id": "T1134",
        "name": "Access Token Manipulation", 
        "platform": "windows",
        "category": "privilege_escalation"
    }
    
    research_context = """
Access token manipulation involves adversaries modifying access tokens to escalate privileges 
or bypass access controls. This technique exploits Windows access token mechanisms to impersonate 
other users or gain system-level access. Common methods include token theft, token impersonation, 
and creating new tokens with elevated privileges.
    """.strip()
    
    print(f"🔄 Generating research output for {technique['id']}...")
    print("   (Note: This requires Ollama to be running)")
    
    # Generate unified research output
    try:
        research_output = generator.generate_unified_research_output(
            technique=technique,
            research_context=research_context,
            sources=["MITRE ATT&CK", "Windows Internals", "Security Research"],
            confidence_score=7.8
        )
        
        if research_output:
            print("✅ Successfully generated research output")
            print(f"   - Quality Score: {research_output.quality_score:.2f}")
            print(f"   - Completeness: {research_output.completeness_score:.2f}")
            print(f"   - Word Count: {research_output.word_count}")
            print(f"   - Has Detection: {bool(research_output.detection.strip())}")
            print(f"   - Has Mitigation: {bool(research_output.mitigation.strip())}")
            
            # Show sample content
            if research_output.description:
                print(f"\n📝 Sample Description (first 200 chars):")
                print(f"   {research_output.description[:200]}...")
                
        else:
            print("❌ Failed to generate research output")
            
    except Exception as e:
        print(f"⚠️ Content generation error (Ollama may not be running): {e}")
    
    print()


def demo_migration_workflow():
    """Demonstrate migration from file-based to JSON-based system."""
    print("🎯 Demo 5: Migration Workflow")
    print("=" * 50)
    
    from autonomous_research.integration.json_output_migration import OutputSystemMigration
    
    # Initialize migration system
    migration = OutputSystemMigration(project_root)
    
    print("🔄 Migration capabilities:")
    print("   - Backup existing file-based outputs")
    print("   - Convert markdown files to JSON objects")
    print("   - Store in Elasticsearch with enhanced metadata")
    print("   - Validate migration success")
    print("   - Provide rollback capabilities")
    
    # Show validation results
    validation_results = migration.validate_migration()
    print(f"\n📋 Current System State:")
    print(f"   - Elasticsearch Outputs: {validation_results.get('total_outputs', 0)}")
    print(f"   - Sample Outputs Available: {len(validation_results.get('sample_outputs', []))}")
    
    if validation_results.get('errors'):
        print(f"   - Errors: {validation_results['errors']}")
    else:
        print("   - No errors detected")
    
    print()


def demo_search_capabilities():
    """Demonstrate advanced search capabilities."""
    print("🎯 Demo 6: Advanced Search Capabilities")
    print("=" * 50)
    
    output_manager = ElasticsearchOutputManager()
    
    if not output_manager.es:
        print("❌ Elasticsearch not available - skipping search demo")
        return
    
    print("🔍 Search Examples:")
    
    # Search by text query
    print("\n1. Text Search for 'privilege escalation':")
    results = output_manager.search_research_outputs(
        query="privilege escalation",
        limit=3
    )
    for output in results:
        print(f"   - {output.technique_id}: {output.technique_name} (Score: {output.quality_score:.2f})")
    
    # Search by platform
    print("\n2. Windows Platform Techniques:")
    results = output_manager.search_research_outputs(
        platform="windows",
        limit=3
    )
    for output in results:
        print(f"   - {output.technique_id}: {output.technique_name} (Platform: {output.platform})")
    
    # Search high-quality outputs
    print("\n3. High Quality Outputs (>0.7):")
    results = output_manager.search_research_outputs(
        min_quality_score=0.7,
        limit=3
    )
    for output in results:
        print(f"   - {output.technique_id}: {output.technique_name} (Quality: {output.quality_score:.2f})")
    
    # Search with detection content
    print("\n4. Outputs with Detection Content:")
    results = output_manager.search_research_outputs(
        has_detection=True,
        limit=3
    )
    for output in results:
        print(f"   - {output.technique_id}: {output.technique_name} (Has Detection: ✅)")
    
    print()


def main():
    """Run all demonstrations."""
    print("🚀 JSON-Based Elasticsearch Output System Demo")
    print("=" * 60)
    print()
    
    # Demo 1: Create research output object
    research_output = demo_research_output_creation()
    
    # Demo 2: Elasticsearch storage
    demo_elasticsearch_storage(research_output)
    
    # Demo 3: Analytics
    demo_analytics_dashboard()
    
    # Demo 4: Content generation
    demo_content_generation()
    
    # Demo 5: Migration workflow
    demo_migration_workflow()
    
    # Demo 6: Search capabilities
    demo_search_capabilities()
    
    print("🎉 Demo Complete!")
    print()
    print("Key Benefits of JSON-Based System:")
    print("✅ Centralized storage in Elasticsearch")
    print("✅ Advanced search and analytics capabilities")
    print("✅ Structured metadata and quality metrics")
    print("✅ Scalable and performant")
    print("✅ API-friendly JSON format")
    print("✅ Version control and archiving")
    print("✅ Real-time updates and collaboration")


if __name__ == "__main__":
    main()
