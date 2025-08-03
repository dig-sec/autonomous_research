#!/usr/bin/env python3
"""
Simple test script to verify the package structure works.
"""

import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

def test_imports():
    """Test that all modules can be imported."""
    
    print("Testing package imports...")
    
    try:
        from src.autonomous_research.core.project_manager import ProjectManager
        print("✓ ProjectManager imported successfully")
    except ImportError as e:
        print(f"✗ ProjectManager import failed: {e}")
    
    try:
        from src.autonomous_research.core.status_manager import StatusManager
        print("✓ StatusManager imported successfully")
    except ImportError as e:
        print(f"✗ StatusManager import failed: {e}")
    
    try:
        from src.autonomous_research.research.summary_manager import ResearchSummaryManager
        print("✓ ResearchSummaryManager imported successfully")
    except ImportError as e:
        print(f"✗ ResearchSummaryManager import failed: {e}")
    
    try:
        from src.autonomous_research.research.external_research import ExternalResearcher
        print("✓ ExternalResearcher imported successfully")
    except ImportError as e:
        print(f"✗ ExternalResearcher import failed: {e}")
    
    try:
        from src.autonomous_research.generation.content_generator import ContentGenerator
        print("✓ ContentGenerator imported successfully")
    except ImportError as e:
        print(f"✗ ContentGenerator import failed: {e}")
    
    try:
        from src.autonomous_research.core.autonomous_system import AutonomousResearchSystem
        print("✓ AutonomousResearchSystem imported successfully")
    except ImportError as e:
        print(f"✗ AutonomousResearchSystem import failed: {e}")

def test_basic_functionality():
    """Test basic functionality."""
    
    print("\nTesting basic functionality...")
    
    try:
        from autonomous_research.core.project_manager import ProjectManager
        
        # Test project manager
        pm = ProjectManager(".")
        stats = pm.get_project_stats()
        print(f"✓ Project stats: {stats}")
        
    except Exception as e:
        print(f"✗ Basic functionality test failed: {e}")

def main():
    """Run all tests."""
    test_imports()
    test_basic_functionality()
    print("\nTest completed!")

if __name__ == "__main__":
    main()
