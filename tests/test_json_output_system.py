#!/usr/bin/env python3
"""
Comprehensive pytest test suite for JSON-based Elasticsearch Output System

Tests all functionality of the new unified JSON output management system.
"""

import pytest
import sys
import os
from datetime import datetime, timezone
from unittest.mock import Mock, patch, MagicMock
import uuid

# Add src to path
sys.path.insert(0, '/home/pabi/git/autonomous_research')
sys.path.insert(0, '/home/pabi/git/autonomous_research/src')

from autonomous_research.output.elasticsearch_output_manager import (
    ResearchOutput, ElasticsearchOutputManager, create_unified_research_output
)
from autonomous_research.generation.enhanced_content_generator import EnhancedContentGenerator


class TestResearchOutput:
    """Test cases for ResearchOutput dataclass"""
    
    def test_research_output_creation(self):
        """Test basic ResearchOutput creation"""
        output = ResearchOutput(
            technique_id="T1055",
            technique_name="Process Injection",
            platform="windows",
            description="Process injection technique for malware persistence",
            detection="Detection using process monitoring",
            mitigation="Apply application isolation",
            agent_notes="Automated analysis completed",
            confidence_score=8.5
        )
        
        assert output.technique_id == "T1055"
        assert output.technique_name == "Process Injection"
        assert output.platform == "windows"
        assert output.confidence_score == 8.5
        assert output.created_at is not None
        
    def test_research_output_defaults(self):
        """Test ResearchOutput with minimal required fields"""
        output = ResearchOutput(
            technique_id="T1134",
            technique_name="Access Token Manipulation",
            platform="windows"
        )
        
        assert output.technique_id == "T1134"
        assert output.description == ""
        assert output.confidence_score == 0.0
        
    def test_research_output_to_dict(self):
        """Test ResearchOutput conversion to dictionary"""
        output = ResearchOutput(
            technique_id="T1055",
            technique_name="Process Injection",
            platform="windows",
            description="Test description"
        )
        
        doc_dict = output.to_elasticsearch_doc()
        
        assert doc_dict["technique_id"] == "T1055"
        assert doc_dict["technique_name"] == "Process Injection"
        assert doc_dict["platform"] == "windows"
        assert doc_dict["description"] == "Test description"
        assert "created_at" in doc_dict
        
    def test_unified_creation_helper(self):
        """Test the create_unified_research_output helper function"""
        technique = {
            'id': 'T1134',
            'name': 'Access Token Manipulation',
            'platform': 'windows'
        }
        
        content_sections = {
            'description': 'Test description content',
            'detection': 'Detection methods',
            'mitigation': 'Mitigation strategies',
            'agent_notes': 'Agent notes'
        }
        
        output = create_unified_research_output(
            technique=technique,
            research_context="Test research context",
            content_sections=content_sections,
            sources=["MITRE", "Blog"],
            confidence_score=8.5
        )
        
        assert output.technique_id == "T1134"
        assert output.description == "Test description content"
        assert output.detection == "Detection methods"
        assert output.confidence_score == 8.5


class TestElasticsearchOutputManager:
    """Test cases for ElasticsearchOutputManager"""
    
    @pytest.fixture
    def mock_es_client(self):
        """Mock Elasticsearch client for testing"""
        mock_client = Mock()
        mock_client.indices.exists.return_value = True
        mock_client.index.return_value = {"_id": "test_doc_id", "result": "created"}
        mock_client.get.return_value = {
            "_source": {
                "technique_id": "T1055",
                "technique_name": "Process Injection",
                "platform": "windows",
                "created_at": "2024-01-01T00:00:00+00:00"
            }
        }
        mock_client.search.return_value = {
            "hits": {
                "total": {"value": 1},
                "hits": [
                    {
                        "_id": "doc1",
                        "_source": {
                            "technique_id": "T1055",
                            "technique_name": "Process Injection",
                            "platform": "windows"
                        }
                    }
                ]
            }
        }
        return mock_client
    
    @pytest.fixture
    def manager(self, mock_es_client):
        """Create ElasticsearchOutputManager with mocked client"""
        with patch('autonomous_research.output.elasticsearch_output_manager.Elasticsearch', return_value=mock_es_client):
            manager = ElasticsearchOutputManager()
            return manager
    
    def test_store_research_output(self, manager, mock_es_client):
        """Test storing a research output"""
        output = ResearchOutput(
            technique_id="T1055",
            technique_name="Process Injection",
            platform="windows",
            description="Test description"
        )
        
        doc_id = manager.store_research_output(output)
        
        assert doc_id == "test_doc_id"
        mock_es_client.index.assert_called_once()
        
    def test_get_research_output(self, manager, mock_es_client):
        """Test retrieving a research output"""
        retrieved_output = manager.get_research_output("test_doc_id")
        
        assert retrieved_output.technique_id == "T1055"
        assert retrieved_output.technique_name == "Process Injection"
        mock_es_client.get.assert_called_once_with(index="research_outputs", id="test_doc_id")
        
    def test_search_by_technique(self, manager, mock_es_client):
        """Test searching by technique ID"""
        results = manager.search_by_technique("T1055")
        
        assert len(results) == 1
        assert results[0]["technique_id"] == "T1055"
        mock_es_client.search.assert_called_once()
        
    def test_search_by_platform(self, manager, mock_es_client):
        """Test searching by platform"""
        results = manager.search_by_platform("windows")
        
        assert len(results) == 1
        mock_es_client.search.assert_called_once()
        
    def test_get_analytics(self, manager, mock_es_client):
        """Test analytics functionality"""
        mock_es_client.search.return_value = {
            "hits": {"total": {"value": 10}},
            "aggregations": {
                "platforms": {
                    "buckets": [
                        {"key": "windows", "doc_count": 7},
                        {"key": "linux", "doc_count": 3}
                    ]
                },
                "avg_confidence": {"value": 7.5},
                "avg_quality": {"value": 0.8}
            }
        }
        
        analytics = manager.get_analytics()
        
        assert analytics["total_documents"] == 10
        assert analytics["platform_distribution"]["windows"] == 7
        assert analytics["average_confidence"] == 7.5
        assert analytics["average_quality"] == 0.8


class TestEnhancedContentGenerator:
    """Test cases for EnhancedContentGenerator"""
    
    @pytest.fixture
    def mock_ollama_client(self):
        """Mock Ollama client for testing"""
        mock_client = Mock()
        mock_client.generate.return_value = {
            'response': 'Generated content for testing'
        }
        return mock_client
    
    @pytest.fixture
    def generator(self, mock_ollama_client):
        """Create EnhancedContentGenerator with mocked dependencies"""
        with patch('autonomous_research.generation.enhanced_content_generator.ollama.Client', return_value=mock_ollama_client):
            with patch('autonomous_research.generation.enhanced_content_generator.ElasticsearchOutputManager') as mock_manager:
                generator = EnhancedContentGenerator()
                generator.output_manager = mock_manager
                return generator
    
    def test_generate_unified_output(self, generator, mock_ollama_client):
        """Test unified output generation"""
        technique_data = {
            'technique_id': 'T1055',
            'name': 'Process Injection',
            'platforms': ['windows'],
            'description': 'Test description'
        }
        
        with patch.object(generator.output_manager, 'store_research_output', return_value="test_doc_id"):
            doc_id = generator.generate_unified_output(technique_data)
            
            assert doc_id == "test_doc_id"
            # Verify Ollama was called for content generation
            assert mock_ollama_client.generate.call_count >= 1
    
    def test_calculate_quality_metrics(self, generator):
        """Test quality metrics calculation"""
        content_sections = {
            'summary': 'This is a comprehensive summary with detailed information about the technique.',
            'detailed_analysis': 'Detailed analysis covering multiple aspects of the security technique.',
            'implementation_details': 'Technical implementation details with code examples.',
            'detection_methods': 'Various detection methods and tools.',
            'mitigation_strategies': 'Effective mitigation strategies.',
            'agent_notes': 'Additional notes and observations.'
        }
        
        quality_score, word_count, completeness = generator.calculate_quality_metrics(content_sections)
        
        assert quality_score > 0
        assert word_count > 0
        assert 0 <= completeness <= 1


class TestIntegration:
    """Integration tests for the complete system"""
    
    def test_end_to_end_workflow(self):
        """Test complete workflow from generation to storage to retrieval"""
        # This would be a more complex integration test
        # For now, we'll test that the components work together
        technique = {
            'id': 'T1055',
            'name': 'Process Injection',
            'platform': 'windows',
            'description': 'Process injection technique'
        }
        
        # Test that we can create a research output
        output = create_unified_research_output(
            technique=technique,
            research_context="Test research context",
            content_sections={
                'description': 'Test description',
                'detection': 'Test detection'
            }
        )
        
        assert output is not None
        assert output.technique_id == 'T1055'


if __name__ == "__main__":
    # Run tests if script is executed directly
    pytest.main([__file__, "-v"])
