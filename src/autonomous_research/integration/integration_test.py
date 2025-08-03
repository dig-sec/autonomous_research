#!/usr/bin/env python3
"""
Integration Test Script

Tests integration of custom techniques with external systems.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

def main():
    """Run integration test."""
    try:
        from src.autonomous_research.knowledge.custom_techniques import CustomTechniqueManager
        manager = CustomTechniqueManager()
        print("Running integration test...")
        # Example: Export to Elasticsearch format
        es_docs = manager.export_to_elasticsearch_format()
        print(f"Exported {len(es_docs)} items for integration.")
    except ImportError as e:
        print(f"❌ Import error: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
