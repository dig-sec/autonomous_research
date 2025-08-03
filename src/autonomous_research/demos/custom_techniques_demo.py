#!/usr/bin/env python3
"""
Simple CLI for Custom Techniques Demo

This demonstrates how to add and manage cybersecurity knowledge that doesn't fit in MITRE ATT&CK.
"""

import sys
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

def main():
    """Simple CLI demo for custom techniques."""
    
    if len(sys.argv) < 2:
        print("Usage: python3 custom_techniques_demo.py <command>")
        print("Commands:")
        print("  stats       - Show statistics")
        print("  cluster     - Create example procedural clusters") 
        print("  emerging    - Add emerging threat example")
        print("  export      - Export to JSON")
        return
    
    command = sys.argv[1]
    
    try:
        from src.autonomous_research.knowledge.custom_techniques import (
            CustomTechniqueManager, CustomTechnique
        )
        
        manager = CustomTechniqueManager()
        
        if command == "stats":
            stats = manager.get_stats()
            print("📊 Custom Techniques Statistics:")
            print(json.dumps(stats, indent=2))
        
        elif command == "cluster":
            print("🎯 Creating example procedural clusters...")
            
            # Example 1 - Memory Injection
            memory_injection_text = """The payload decompresses executable code in memory using advanced compression techniques.
It then injects the code into target processes using process hollowing and thread hijacking methods.
The injected code operates within legitimate process contexts to maintain stealth and avoid detection."""
            
            # Example 2 - Data Collection  
            data_collection_text = """The system enumerates network configurations and installed software packages systematically.
It compiles comprehensive system information including running processes, services, and security tools.
The collected data is prepared for exfiltration through encrypted communication channels with C2 infrastructure."""
            
            memory_cluster_id = manager.create_procedural_cluster_from_text(
                memory_injection_text, "Memory Injection Procedures"
            )
            data_cluster_id = manager.create_procedural_cluster_from_text(
                data_collection_text, "Data Collection Procedures"
            )
            
            print(f"✅ Created memory injection cluster: {memory_cluster_id}")
            print(f"✅ Created data collection cluster: {data_cluster_id}")
        
        elif command == "emerging":
            print("🔥 Adding emerging threat example...")
            
            emerging_threat = CustomTechnique(
                id='',
                name='AI-Powered Social Engineering',
                description='Use of advanced AI models to craft personalized phishing campaigns and social engineering attacks that adapt in real-time based on victim responses.',
                category='emerging_threat',
                platforms=['web', 'mobile', 'windows', 'linux', 'macos'],
                severity='high',
                sources=['threat_intelligence_reports', 'security_conferences'],
                tags=['ai', 'social_engineering', 'emerging', 'phishing']
            )
            
            technique_id = manager.add_custom_technique(emerging_threat)
            print(f"✅ Added emerging threat: {technique_id}")
        
        elif command == "export":
            es_docs = manager.export_to_elasticsearch_format()
            output_file = 'custom_techniques_export.json'
            with open(output_file, 'w') as f:
                json.dump(es_docs, f, indent=2)
            print(f"✅ Exported {len(es_docs)} items to {output_file}")
        
        else:
            print(f"❌ Unknown command: {command}")
    
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Custom techniques module may not be available")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
