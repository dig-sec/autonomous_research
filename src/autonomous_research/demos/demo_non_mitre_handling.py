#!/usr/bin/env python3
"""
Demo: Handling Non-MITRE Techniques

Shows how to add, cluster, and analyze techniques not covered by MITRE ATT&CK.
"""

import sys
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

def main():
    """Demo for handling non-MITRE techniques."""
    try:
        from src.autonomous_research.knowledge.custom_techniques import CustomTechniqueManager, CustomTechnique
        manager = CustomTechniqueManager()
        print("Adding non-MITRE technique example...")
        technique = CustomTechnique(
            id='',
            name='Cloud Container Escape',
            description='Techniques for escaping from cloud containers to host environments, not covered by MITRE.',
            category='cloud',
            platforms=['aws', 'azure', 'gcp', 'linux'],
            severity='critical',
            sources=['cloud_security_reports'],
            tags=['container', 'escape', 'cloud', 'non-mitre']
        )
        tid = manager.add_custom_technique(technique)
        print(f"✅ Added: {tid}")
        print("Clustering...")
        cluster_id = manager.create_procedural_cluster_from_text(
            "Container escape using kernel exploits and misconfigured privileges.",
            "Cloud Container Escape Procedures"
        )
        print(f"✅ Cluster created: {cluster_id}")
        print("Statistics:")
        print(json.dumps(manager.get_stats(), indent=2))
    except ImportError as e:
        print(f"❌ Import error: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
