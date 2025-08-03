#!/usr/bin/env python3
"""
Simple integration test for JSON-based output system

Demonstrates that the core functionality works without complex mocking.
"""

import sys
import os
sys.path.insert(0, '/home/pabi/git/autonomous_research')
sys.path.insert(0, '/home/pabi/git/autonomous_research/src')

from autonomous_research.output.elasticsearch_output_manager import (
    ResearchOutput, create_unified_research_output
)


def test_basic_functionality():
    """Test basic functionality without Elasticsearch"""
    print("🚀 Testing JSON Output System Core Functionality")
    print("=" * 60)
    
    # Test 1: ResearchOutput creation
    print("\n🧪 Test 1: ResearchOutput Creation")
    try:
        output = ResearchOutput(
            technique_id="T1055",
            technique_name="Process Injection",
            platform="windows",
            description="Advanced process injection technique",
            detection="Monitor process creation and DLL loading",
            mitigation="Apply code signing and process isolation",
            agent_notes="High-priority technique for red team exercises",
            confidence_score=8.5
        )
        
        print(f"✅ Created ResearchOutput: {output.technique_id}")
        print(f"   - Name: {output.technique_name}")
        print(f"   - Platform: {output.platform}")
        print(f"   - Confidence: {output.confidence_score}")
        print(f"   - Created: {output.created_at}")
        
        # Test quality metrics calculation
        output.calculate_metrics()
        print(f"   - Word Count: {output.word_count}")
        print(f"   - Completeness: {output.completeness_score:.2f}")
        
    except Exception as e:
        print(f"❌ ResearchOutput creation failed: {e}")
        return False
    
    # Test 2: Document conversion
    print("\n🧪 Test 2: Document Conversion")
    try:
        doc_dict = output.to_elasticsearch_doc()
        
        required_fields = ['technique_id', 'technique_name', 'platform', 'created_at']
        for field in required_fields:
            if field not in doc_dict:
                raise ValueError(f"Missing required field: {field}")
        
        print(f"✅ Document conversion successful")
        print(f"   - Fields: {len(doc_dict.keys())}")
        print(f"   - Required fields present: {all(f in doc_dict for f in required_fields)}")
        
    except Exception as e:
        print(f"❌ Document conversion failed: {e}")
        return False
    
    # Test 3: Unified creation helper
    print("\n🧪 Test 3: Unified Creation Helper")
    try:
        technique = {
            'id': 'T1134',
            'name': 'Access Token Manipulation',
            'platform': 'windows'
        }
        
        content_sections = {
            'description': 'Adversaries may modify access tokens to operate under a different user context.',
            'detection': 'Monitor for unusual token manipulation activities.',
            'mitigation': 'Implement proper access controls and monitoring.',
            'purple_playbook': 'Test token manipulation detection capabilities.',
            'references': 'MITRE ATT&CK T1134, Windows Security Documentation',
            'agent_notes': 'Critical technique for privilege escalation scenarios.'
        }
        
        unified_output = create_unified_research_output(
            technique=technique,
            research_context="Automated research for red team exercise planning",
            content_sections=content_sections,
            sources=["MITRE ATT&CK", "Microsoft Documentation", "Security Research"],
            confidence_score=9.0
        )
        
        print(f"✅ Unified creation successful")
        print(f"   - Technique: {unified_output.technique_id} - {unified_output.technique_name}")
        print(f"   - Platform: {unified_output.platform}")
        print(f"   - Confidence: {unified_output.confidence_score}")
        print(f"   - Source Count: {unified_output.source_count}")
        
        # Calculate metrics for the unified output
        unified_output.calculate_metrics()
        print(f"   - Word Count: {unified_output.word_count}")
        print(f"   - Completeness: {unified_output.completeness_score:.2f}")
        
    except Exception as e:
        print(f"❌ Unified creation failed: {e}")
        return False
    
    # Test 4: Data validation
    print("\n🧪 Test 4: Data Validation")
    try:
        # Test that required fields are present
        assert output.technique_id == "T1055"
        assert output.technique_name == "Process Injection"
        assert output.platform == "windows"
        assert output.confidence_score == 8.5
        assert output.created_at is not None
        
        # Test that metrics are calculated correctly
        assert output.word_count > 0
        assert 0 <= output.completeness_score <= 1
        
        # Test unified output
        assert unified_output.technique_id == "T1134"
        assert unified_output.confidence_score == 9.0
        assert unified_output.source_count == 3
        
        print(f"✅ All validation checks passed")
        
    except AssertionError as e:
        print(f"❌ Validation failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Validation error: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("🎯 Summary: All core functionality tests PASSED")
    print("✅ The JSON output system is working correctly!")
    print("\nNext Steps:")
    print("- Test with real Elasticsearch connection")
    print("- Test content generation integration")
    print("- Test search and analytics functionality")
    
    return True


if __name__ == "__main__":
    success = test_basic_functionality()
    exit(0 if success else 1)
