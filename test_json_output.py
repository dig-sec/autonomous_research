#!/usr/bin/env python3
"""
Test script for JSON-based Elasticsearch Output System

Tests the core functionality of the new JSON output management system.
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, '/home/pabi/git/autonomous_research')
sys.path.insert(0, '/home/pabi/git/autonomous_research/src')

def test_basic_imports():
    """Test that all modules can be imported correctly."""
    print("🧪 Test 1: Basic Imports")
    try:
        from autonomous_research.output.elasticsearch_output_manager import (
            ResearchOutput, ElasticsearchOutputManager, create_unified_research_output
        )
        print("✅ Import successful")
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_research_output_creation():
    """Test ResearchOutput object creation and metrics calculation."""
    print("\n🧪 Test 2: ResearchOutput Creation")
    try:
        from autonomous_research.output.elasticsearch_output_manager import ResearchOutput
        
        # Create test output
        output = ResearchOutput(
            technique_id='T1055',
            technique_name='Process Injection',
            platform='windows',
            category='defense_evasion',
            description='Process injection allows execution in another process address space.',
            detection='Monitor for unusual process behavior and memory allocations.',
            mitigation='Implement process monitoring and endpoint detection.',
            purple_playbook='Test process injection detection capabilities.',
            references='MITRE ATT&CK T1055, Security research papers.',
            agent_notes='High confidence research with multiple validated sources.'
        )
        
        print(f"✅ Created ResearchOutput: {output.technique_id}")
        print(f"   - Technique: {output.technique_name}")
        print(f"   - Platform: {output.platform}")
        print(f"   - Quality Score: {output.quality_score:.2f}")
        print(f"   - Completeness: {output.completeness_score:.2f}")
        print(f"   - Word Count: {output.word_count}")
        print(f"   - Created: {output.created_at}")
        
        # Validate metrics
        assert output.word_count > 0, "Word count should be greater than 0"
        assert 0 <= output.quality_score <= 1, "Quality score should be between 0 and 1"
        assert 0 <= output.completeness_score <= 1, "Completeness should be between 0 and 1"
        assert output.completeness_score == 1.0, "All sections filled, should be 100% complete"
        
        print("✅ Metrics validation passed")
        return output
        
    except Exception as e:
        print(f"❌ ResearchOutput creation failed: {e}")
        return None

def test_elasticsearch_document_conversion(output):
    """Test conversion to Elasticsearch document format."""
    print("\n🧪 Test 3: Elasticsearch Document Conversion")
    try:
        doc = output.to_elasticsearch_doc()
        
        # Validate document structure
        required_fields = [
            'technique_id', 'technique_name', 'platform', 'category',
            'description', 'detection', 'mitigation', 'purple_playbook',
            'quality_score', 'completeness_score', 'word_count',
            'has_detection', 'has_mitigation', 'is_complete', 'is_high_quality'
        ]
        
        for field in required_fields:
            assert field in doc, f"Missing required field: {field}"
        
        print(f"✅ Document conversion successful")
        print(f"   - Fields: {len(doc)} total")
        print(f"   - Has detection: {doc['has_detection']}")
        print(f"   - Has mitigation: {doc['has_mitigation']}")
        print(f"   - Is complete: {doc['is_complete']}")
        print(f"   - Is high quality: {doc['is_high_quality']}")
        
        return doc
        
    except Exception as e:
        print(f"❌ Document conversion failed: {e}")
        return None

def test_elasticsearch_manager():
    """Test ElasticsearchOutputManager initialization."""
    print("\n🧪 Test 4: ElasticsearchOutputManager")
    try:
        from autonomous_research.output.elasticsearch_output_manager import ElasticsearchOutputManager
        
        manager = ElasticsearchOutputManager()
        
        if manager.es is None:
            print("⚠️  Elasticsearch not available - manager created but not connected")
            print("   - This is expected if Elasticsearch is not running")
            return manager
        else:
            print("✅ ElasticsearchOutputManager created successfully")
            print(f"   - Output index: {manager.output_index}")
            print(f"   - Archive index: {manager.archive_index}")
            print("   - Elasticsearch connection: ✅")
            return manager
            
    except Exception as e:
        print(f"❌ ElasticsearchOutputManager creation failed: {e}")
        return None

def test_storage_and_retrieval(manager, output):
    """Test storing and retrieving research outputs."""
    print("\n🧪 Test 5: Storage and Retrieval")
    
    if manager.es is None:
        print("⚠️  Skipping storage tests - Elasticsearch not available")
        return False
    
    try:
        # Test storage
        print("   Testing storage...")
        success = manager.store_research_output(output)
        
        if success:
            print("✅ Storage successful")
            
            # Test retrieval
            print("   Testing retrieval...")
            retrieved = manager.get_research_output(output.technique_id, output.platform)
            
            if retrieved:
                print("✅ Retrieval successful")
                print(f"   - Retrieved: {retrieved.technique_name}")
                print(f"   - Quality: {retrieved.quality_score:.2f}")
                print(f"   - Word count: {retrieved.word_count}")
                
                # Validate data integrity
                assert retrieved.technique_id == output.technique_id
                assert retrieved.technique_name == output.technique_name
                assert retrieved.platform == output.platform
                print("✅ Data integrity verified")
                
                return True
            else:
                print("❌ Retrieval failed")
                return False
        else:
            print("❌ Storage failed")
            return False
            
    except Exception as e:
        print(f"❌ Storage/retrieval test failed: {e}")
        return False

def test_search_functionality(manager):
    """Test search capabilities."""
    print("\n🧪 Test 6: Search Functionality")
    
    if manager.es is None:
        print("⚠️  Skipping search tests - Elasticsearch not available")
        return False
    
    try:
        # Test basic search
        print("   Testing text search...")
        results = manager.search_research_outputs(
            query="process injection",
            limit=5
        )
        
        print(f"✅ Text search returned {len(results)} results")
        for result in results[:3]:  # Show first 3
            print(f"   - {result.technique_id}: {result.technique_name}")
        
        # Test platform filter
        print("   Testing platform filter...")
        windows_results = manager.search_research_outputs(
            platform="windows",
            limit=5
        )
        
        print(f"✅ Platform filter returned {len(windows_results)} results")
        
        # Test quality filter
        print("   Testing quality filter...")
        quality_results = manager.search_research_outputs(
            min_quality_score=0.5,
            limit=5
        )
        
        print(f"✅ Quality filter returned {len(quality_results)} results")
        
        return True
        
    except Exception as e:
        print(f"❌ Search test failed: {e}")
        return False

def test_analytics(manager):
    """Test analytics functionality."""
    print("\n🧪 Test 7: Analytics")
    
    if manager.es is None:
        print("⚠️  Skipping analytics tests - Elasticsearch not available")
        return False
    
    try:
        analytics = manager.get_analytics_summary()
        
        print("✅ Analytics retrieved successfully")
        print(f"   - Total outputs: {analytics.get('total_outputs', 0)}")
        print(f"   - Average quality: {analytics.get('avg_quality_score', 0):.2f}")
        print(f"   - Complete outputs: {analytics.get('complete_outputs', 0)}")
        print(f"   - High quality outputs: {analytics.get('high_quality_outputs', 0)}")
        
        # Show platform distribution
        platforms = analytics.get('platforms', {})
        if platforms:
            print("   - Platform distribution:")
            for platform, count in platforms.items():
                print(f"     • {platform}: {count}")
        
        return True
        
    except Exception as e:
        print(f"❌ Analytics test failed: {e}")
        return False

def test_unified_creation_helper():
    """Test the create_unified_research_output helper function."""
    print("\n🧪 Test 8: Unified Creation Helper")
    try:
        from autonomous_research.output.elasticsearch_output_manager import create_unified_research_output
        
        technique = {
            "id": "T1134",
            "name": "Access Token Manipulation",
            "platform": "windows",
            "category": "privilege_escalation"
        }
        
        content_sections = {
            "description": "Access token manipulation involves modifying access tokens to escalate privileges.",
            "detection": "Monitor for unusual token operations and privilege changes.",
            "mitigation": "Implement least privilege principles and token monitoring.",
            "purple_playbook": "Test token manipulation detection and response.",
            "references": "MITRE ATT&CK T1134",
            "agent_notes": "High confidence assessment based on technical analysis."
        }
        
        output = create_unified_research_output(
            technique=technique,
            research_context="Comprehensive token manipulation analysis",
            content_sections=content_sections,
            sources=["MITRE ATT&CK", "Windows Documentation", "Security Research"],
            confidence_score=8.5
        )
        
        print("✅ Unified creation successful")
        print(f"   - Technique: {output.technique_id} - {output.technique_name}")
        print(f"   - Sources: {len(output.sources or [])}")
        print(f"   - Confidence: {output.confidence_score}")
        print(f"   - Quality: {output.quality_score:.2f}")
        
        return output
        
    except Exception as e:
        print(f"❌ Unified creation test failed: {e}")
        return None

def main():
    """Run all tests."""
    print("🚀 JSON-Based Elasticsearch Output System Tests")
    print("=" * 60)
    
    results = []
    
    # Test 1: Basic imports
    results.append(test_basic_imports())
    
    # Test 2: ResearchOutput creation
    output = test_research_output_creation()
    results.append(output is not None)
    
    if output:
        # Test 3: Document conversion
        doc = test_elasticsearch_document_conversion(output)
        results.append(doc is not None)
        
        # Test 4: Manager initialization
        manager = test_elasticsearch_manager()
        results.append(manager is not None)
        
        if manager:
            # Test 5: Storage and retrieval
            results.append(test_storage_and_retrieval(manager, output))
            
            # Test 6: Search functionality
            results.append(test_search_functionality(manager))
            
            # Test 7: Analytics
            results.append(test_analytics(manager))
    
    # Test 8: Unified creation helper
    unified_output = test_unified_creation_helper()
    results.append(unified_output is not None)
    
    # Results summary
    print("\n" + "=" * 60)
    print("🎯 Test Results Summary")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"✅ Passed: {passed}/{total} tests")
    
    if passed == total:
        print("🎉 All tests passed! JSON output system is working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Check Elasticsearch connectivity if storage tests failed.")
        return 1

if __name__ == "__main__":
    exit(main())
