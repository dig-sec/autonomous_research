#!/usr/bin/env python3
"""
Integration Status CLI

Shows status of integration between custom techniques and other systems.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

def main():
    """Show integration status."""
    try:
        from src.autonomous_research.knowledge.custom_techniques import CustomTechniqueManager
        manager = CustomTechniqueManager()
        print("Integration status:")
        # Example: Check if clusters are ready for export
        clusters = manager.get_procedural_clusters()
        ready = [c for c in clusters if c.coherence > 0.7]
        print(f"Clusters ready for export: {len(ready)}")
        print(f"Total clusters: {len(clusters)}")
    except ImportError as e:
        print(f"❌ Import error: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
