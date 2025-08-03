#!/usr/bin/env python3
"""
Advanced Clustering Analysis Demo

This demonstrates the enhanced clustering capabilities with dynamic statistics
and insights generation from queried data.
"""

import sys
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

def main():
    """Advanced clustering analysis demonstration."""
    
    if len(sys.argv) < 2:
        print("Usage: python3 clustering_analysis.py <command>")
        print("Commands:")
        print("  stats       - Show comprehensive statistics")
        print("  insights    - Show clustering insights") 
        print("  recommendations - Get clustering recommendations")
        print("  quality     - Analyze cluster quality")
        print("  create      - Create sample clusters for analysis")
        return
    
    command = sys.argv[1]
    
    try:
        from src.autonomous_research.knowledge.custom_techniques import (
            CustomTechniqueManager, CustomTechnique
        )
        
        manager = CustomTechniqueManager()
        
        if command == "stats":
            print("📊 Comprehensive Statistics (Queried from Data):")
            stats = manager.get_stats()
            print(json.dumps(stats, indent=2))
        
        elif command == "insights":
            print("🔍 Clustering Insights:")
            insights = manager.get_cluster_insights()
            print(json.dumps(insights, indent=2))
        
        elif command == "recommendations":
            print("💡 Clustering Recommendations:")
            recommendations = manager.get_clustering_recommendations()
            for i, rec in enumerate(recommendations, 1):
                print(f"  {i}. {rec}")
        
        elif command == "quality":
            print("📈 Cluster Quality Analysis:")
            stats = manager.get_stats()
            
            if "cluster_analysis" in stats:
                analysis = stats["cluster_analysis"]
                print(f"Total Clusters: {stats['total_procedural_clusters']}")
                print(f"Average Coherence: {stats['average_cluster_coherence']:.3f}")
                print(f"Best Coherence: {analysis['max_coherence']:.3f}")
                print(f"Worst Coherence: {analysis['min_coherence']:.3f}")
                print(f"High Quality Clusters: {analysis['clusters_with_high_coherence']}")
                print(f"Clusters Needing Work: {analysis['clusters_needing_refinement']}")
                
                # Show coherence distribution
                print("\nCoherence Distribution:")
                for coherence_group, count in stats["clusters_by_coherence"].items():
                    print(f"  {coherence_group}: {count} clusters")
            else:
                print("No cluster analysis data available")
        
        elif command == "create":
            print("🏗️  Creating sample clusters for analysis...")
            
            # Create diverse clusters with different quality levels
            clusters_to_create = [
                {
                    "text": """Network reconnaissance using automated scanning tools and manual enumeration techniques.
                    The attacker performs port scanning, service detection, and vulnerability assessment.
                    Information gathered includes network topology, running services, and potential attack vectors.""",
                    "name": "Network Reconnaissance Procedures"
                },
                {
                    "text": """Data exfiltration through encrypted communication channels and steganographic techniques.
                    Sensitive files are compressed, encrypted, and transmitted via covert channels.
                    The process includes data staging, encryption, and secure transmission to external servers.""",
                    "name": "Data Exfiltration Procedures"
                },
                {
                    "text": """Persistence mechanism establishment using registry modifications and scheduled tasks.
                    The malware creates multiple persistence points to ensure system survival.
                    Methods include startup folder entries, registry run keys, and service installations.""",
                    "name": "Persistence Establishment"
                },
                {
                    "text": """Credential harvesting from memory dumps and password stores.
                    Tools extract credentials from LSASS, browser password stores, and cached credentials.
                    The process involves memory dumping, credential extraction, and privilege escalation.""",
                    "name": "Credential Harvesting"
                }
            ]
            
            created_clusters = []
            for cluster_data in clusters_to_create:
                cluster_id = manager.create_procedural_cluster_from_text(
                    cluster_data["text"], cluster_data["name"]
                )
                created_clusters.append(cluster_id)
                print(f"✅ Created: {cluster_id} - {cluster_data['name']}")
            
            print(f"\n📊 Created {len(created_clusters)} new clusters")
            
            # Show updated stats
            new_stats = manager.get_stats()
            print(f"Total clusters now: {new_stats['total_procedural_clusters']}")
            print(f"New average coherence: {new_stats['average_cluster_coherence']:.3f}")
        
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
        print("Usage: python3 clustering_analysis.py <command>")
        print("Commands:")
        print("  stats       - Show comprehensive statistics")
        print("  insights    - Show clustering insights") 
        print("  recommendations - Get clustering recommendations")
        print("  quality     - Analyze cluster quality")
        print("  create      - Create sample clusters for analysis")
        return
    
    command = sys.argv[1]
    
    try:
        from src.autonomous_research.knowledge.custom_techniques import (
            CustomTechniqueManager, CustomTechnique
        )
        
        manager = CustomTechniqueManager()
        
        if command == "stats":
            print("📊 Comprehensive Statistics (Queried from Data):")
            stats = manager.get_stats()
            print(json.dumps(stats, indent=2))
        
        elif command == "insights":
            print("🔍 Clustering Insights:")
            insights = manager.get_cluster_insights()
            print(json.dumps(insights, indent=2))
        
        elif command == "recommendations":
            print("💡 Clustering Recommendations:")
            recommendations = manager.get_clustering_recommendations()
            for i, rec in enumerate(recommendations, 1):
                print(f"  {i}. {rec}")
        
        elif command == "quality":
            print("📈 Cluster Quality Analysis:")
            stats = manager.get_stats()
            
            if "cluster_analysis" in stats:
                analysis = stats["cluster_analysis"]
                print(f"Total Clusters: {stats['total_procedural_clusters']}")
                print(f"Average Coherence: {stats['average_cluster_coherence']:.3f}")
                print(f"Best Coherence: {analysis['max_coherence']:.3f}")
                print(f"Worst Coherence: {analysis['min_coherence']:.3f}")
                print(f"High Quality Clusters: {analysis['clusters_with_high_coherence']}")
                print(f"Clusters Needing Work: {analysis['clusters_needing_refinement']}")
                
                # Show coherence distribution
                print("\nCoherence Distribution:")
                for coherence_group, count in stats["clusters_by_coherence"].items():
                    print(f"  {coherence_group}: {count} clusters")
            else:
                print("No cluster analysis data available")
        
        elif command == "create":
            print("🏗️  Creating sample clusters for analysis...")
            
            # Create diverse clusters with different quality levels
            clusters_to_create = [
                {
                    "text": """Network reconnaissance using automated scanning tools and manual enumeration techniques.
                    The attacker performs port scanning, service detection, and vulnerability assessment.
                    Information gathered includes network topology, running services, and potential attack vectors.""",
                    "name": "Network Reconnaissance Procedures"
                },
                {
                    "text": """Data exfiltration through encrypted communication channels and steganographic techniques.
                    Sensitive files are compressed, encrypted, and transmitted via covert channels.
                    The process includes data staging, encryption, and secure transmission to external servers.""",
                    "name": "Data Exfiltration Procedures"
                },
                {
                    "text": """Persistence mechanism establishment using registry modifications and scheduled tasks.
                    The malware creates multiple persistence points to ensure system survival.
                    Methods include startup folder entries, registry run keys, and service installations.""",
                    "name": "Persistence Establishment"
                },
                {
                    "text": """Credential harvesting from memory dumps and password stores.
                    Tools extract credentials from LSASS, browser password stores, and cached credentials.
                    The process involves memory dumping, credential extraction, and privilege escalation.""",
                    "name": "Credential Harvesting"
                }
            ]
            
            created_clusters = []
            for cluster_data in clusters_to_create:
                cluster_id = manager.create_procedural_cluster_from_text(
                    cluster_data["text"], cluster_data["name"]
                )
                created_clusters.append(cluster_id)
                print(f"✅ Created: {cluster_id} - {cluster_data['name']}")
            
            print(f"\n📊 Created {len(created_clusters)} new clusters")
            
            # Show updated stats
            new_stats = manager.get_stats()
            print(f"Total clusters now: {new_stats['total_procedural_clusters']}")
            print(f"New average coherence: {new_stats['average_cluster_coherence']:.3f}")
        
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
