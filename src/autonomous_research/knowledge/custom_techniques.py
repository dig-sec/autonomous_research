#!/usr/bin/env python3
"""
Custom Techniques Manager for Non-MITRE Attack Patterns

This module handles cybersecurity knowledge that doesn't fit into the MITRE ATT&CK framework,
including:
- Custom attack patterns
- Emerging threats
- Industry-specific techniques
- Tool-specific behaviors
- Procedural clusters
- Zero-day techniques
- Living-off-the-land techniques not covered by MITRE
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import hashlib
import re

try:
    from ..config.secure_config import get_config
except ImportError:
    # Fallback for standalone usage
    def get_config():
        return {}


@dataclass
class CustomTechnique:
    """Represents a custom technique not covered by MITRE ATT&CK."""
    id: str
    name: str
    description: str
    category: str  # e.g., "emerging_threat", "tool_specific", "procedural_cluster"
    subcategory: Optional[str] = None
    platforms: Optional[List[str]] = None
    detection_difficulty: str = "medium"  # low, medium, high, very_high
    severity: str = "medium"  # low, medium, high, critical
    sources: Optional[List[str]] = None
    related_mitre_techniques: Optional[List[str]] = None
    procedural_cluster_id: Optional[str] = None
    cosine_distance_threshold: Optional[float] = None
    created_date: Optional[str] = None
    updated_date: Optional[str] = None
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if not self.created_date:
            self.created_date = datetime.now().isoformat()
        if not self.updated_date:
            self.updated_date = self.created_date
        if not self.platforms:
            self.platforms = ["unknown"]
        if not self.sources:
            self.sources = []
        if not self.related_mitre_techniques:
            self.related_mitre_techniques = []
        if not self.tags:
            self.tags = []
        if not self.metadata:
            self.metadata = {}


@dataclass
class ProceduralCluster:
    """Represents a cluster of related procedures with cosine distance metrics."""
    cluster_id: str
    name: str
    description: str
    procedures: List[str]  # List of procedure descriptions
    cosine_distances: Dict[str, float]  # Procedure hash -> cosine distance
    centroid_procedure: str  # The most representative procedure
    related_techniques: List[str]  # MITRE or custom technique IDs
    cluster_size: int
    coherence_score: float  # How tightly related the procedures are
    created_date: str
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if not self.metadata:
            self.metadata = {}
        self.cluster_size = len(self.procedures)


class CustomTechniqueManager:
    """Manages custom techniques and procedural clusters."""

    def __init__(self, project_root: Optional[str] = None):
        self.config = get_config()
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.custom_techniques_file = self.project_root / "data" / "custom_techniques.json"
        self.procedural_clusters_file = self.project_root / "data" / "procedural_clusters.json"
        self.logger = logging.getLogger(__name__)
        
        # Ensure data directory exists
        self.custom_techniques_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize storage
        self.custom_techniques: Dict[str, CustomTechnique] = {}
        self.procedural_clusters: Dict[str, ProceduralCluster] = {}
        
        # Load existing data
        self._load_data()

    def _load_data(self):
        """Load custom techniques and procedural clusters from disk."""
        try:
            if self.custom_techniques_file.exists():
                with open(self.custom_techniques_file, 'r') as f:
                    data = json.load(f)
                    for tech_id, tech_data in data.items():
                        self.custom_techniques[tech_id] = CustomTechnique(**tech_data)
                self.logger.info(f"Loaded {len(self.custom_techniques)} custom techniques")

            if self.procedural_clusters_file.exists():
                with open(self.procedural_clusters_file, 'r') as f:
                    data = json.load(f)
                    for cluster_id, cluster_data in data.items():
                        self.procedural_clusters[cluster_id] = ProceduralCluster(**cluster_data)
                self.logger.info(f"Loaded {len(self.procedural_clusters)} procedural clusters")

        except Exception as e:
            self.logger.error(f"Error loading custom techniques data: {e}")

    def _save_data(self):
        """Save custom techniques and procedural clusters to disk."""
        try:
            # Save custom techniques
            custom_tech_data = {
                tech_id: asdict(technique) 
                for tech_id, technique in self.custom_techniques.items()
            }
            with open(self.custom_techniques_file, 'w') as f:
                json.dump(custom_tech_data, f, indent=2)

            # Save procedural clusters
            cluster_data = {
                cluster_id: asdict(cluster) 
                for cluster_id, cluster in self.procedural_clusters.items()
            }
            with open(self.procedural_clusters_file, 'w') as f:
                json.dump(cluster_data, f, indent=2)

            self.logger.info("Saved custom techniques and procedural clusters")

        except Exception as e:
            self.logger.error(f"Error saving custom techniques data: {e}")

    def generate_custom_id(self, name: str, category: str) -> str:
        """Generate a unique ID for a custom technique."""
        # Create a hash of the name and category
        content = f"{name}_{category}_{datetime.now().isoformat()}"
        hash_obj = hashlib.md5(content.encode())
        hash_hex = hash_obj.hexdigest()[:8]
        
        # Format as custom technique ID
        category_prefix = {
            "emerging_threat": "ET",
            "tool_specific": "TS", 
            "procedural_cluster": "PC",
            "zero_day": "ZD",
            "living_off_land": "LOL",
            "industry_specific": "IS",
            "custom_malware": "CM",
            "unknown": "UK"
        }.get(category, "CU")
        
        return f"{category_prefix}{hash_hex.upper()}"

    def add_custom_technique(self, technique: CustomTechnique) -> str:
        """Add a new custom technique."""
        if not technique.id:
            technique.id = self.generate_custom_id(technique.name, technique.category)
        
        technique.updated_date = datetime.now().isoformat()
        self.custom_techniques[technique.id] = technique
        self._save_data()
        
        self.logger.info(f"Added custom technique: {technique.id} - {technique.name}")
        return technique.id

    def add_procedural_cluster(self, cluster: ProceduralCluster) -> str:
        """Add a new procedural cluster."""
        cluster.created_date = datetime.now().isoformat()
        self.procedural_clusters[cluster.cluster_id] = cluster
        self._save_data()
        
        self.logger.info(f"Added procedural cluster: {cluster.cluster_id} - {cluster.name}")
        return cluster.cluster_id

    def create_procedural_cluster_from_text(self, cluster_text: str, cluster_name: Optional[str] = None) -> str:
        """
        Create a procedural cluster from text description.
        
        Example input:
        "The shellcode then decompresses a DLL in memory using advanced techniques.
         It then injects the payload into the target process using API calls..."
        """
        # Extract individual procedures
        procedures = self._extract_procedures_from_text(cluster_text)
        
        # Generate cluster ID
        cluster_id = f"PC{hashlib.md5(cluster_text.encode()).hexdigest()[:8].upper()}"
        
        # Calculate cosine distances (simplified for now)
        cosine_distances = self._calculate_procedure_distances(procedures)
        
        # Find centroid procedure (most representative)
        centroid = self._find_centroid_procedure(procedures, cosine_distances)
        
        # Create cluster
        cluster = ProceduralCluster(
            cluster_id=cluster_id,
            name=cluster_name or f"Cluster {cluster_id}",
            description=f"Procedural cluster extracted from: {cluster_text[:100]}...",
            procedures=procedures,
            cosine_distances=cosine_distances,
            centroid_procedure=centroid,
            related_techniques=[],
            cluster_size=len(procedures),
            coherence_score=self._calculate_coherence_score(cosine_distances),
            created_date=datetime.now().isoformat()
        )
        
        return self.add_procedural_cluster(cluster)

    def _extract_procedures_from_text(self, text: str) -> List[str]:
        """Extract individual procedures from text."""
        # Split on sentence boundaries and clean up
        sentences = re.split(r'[.!?]+', text)
        procedures = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 20:  # Filter out very short fragments
                procedures.append(sentence)
        
        return procedures

    def _calculate_procedure_distances(self, procedures: List[str]) -> Dict[str, float]:
        """Calculate cosine distances between procedures (simplified)."""
        distances = {}
        for i, procedure in enumerate(procedures):
            # Simple hash-based distance for now
            # In a real implementation, you'd use proper NLP/embeddings
            proc_hash = hashlib.md5(procedure.encode()).hexdigest()
            # Simulate cosine distance (0.0 to 1.0)
            distance = (int(proc_hash[:2], 16) / 255.0)
            distances[proc_hash] = distance
        
        return distances

    def _find_centroid_procedure(self, procedures: List[str], distances: Dict[str, float]) -> str:
        """Find the most representative procedure in the cluster."""
        if not procedures:
            return ""
        
        # For now, return the longest procedure as centroid
        # In a real implementation, you'd calculate the actual centroid
        return max(procedures, key=len)

    def _calculate_coherence_score(self, distances: Dict[str, float]) -> float:
        """Calculate how coherent/tight the cluster is."""
        if not distances:
            return 0.0
        
        avg_distance = sum(distances.values()) / len(distances)
        # Lower average distance = higher coherence
        return 1.0 - avg_distance

    def identify_emerging_threat(self, description: str, sources: List[str]) -> str:
        """Identify and catalog an emerging threat not in MITRE."""
        # Extract key characteristics
        name = self._extract_threat_name(description)
        platforms = self._extract_platforms(description)
        severity = self._assess_severity(description)
        
        technique = CustomTechnique(
            id="",  # Will be auto-generated
            name=name,
            description=description,
            category="emerging_threat",
            platforms=platforms,
            severity=severity,
            sources=sources,
            tags=["emerging", "unclassified"]
        )
        
        return self.add_custom_technique(technique)

    def identify_tool_specific_behavior(self, tool_name: str, behavior: str, 
                                       related_mitre: Optional[List[str]] = None) -> str:
        """Catalog tool-specific behaviors not covered by MITRE."""
        technique = CustomTechnique(
            id="",
            name=f"{tool_name} - {behavior[:50]}",
            description=behavior,
            category="tool_specific",
            subcategory=tool_name,
            related_mitre_techniques=related_mitre or [],
            tags=["tool-specific", tool_name.lower()]
        )
        
        return self.add_custom_technique(technique)

    def _extract_threat_name(self, description: str) -> str:
        """Extract a threat name from description."""
        # Simple extraction - look for capitalized words/phrases
        words = description.split()[:10]  # First 10 words
        capitalized = [w for w in words if w[0].isupper() and len(w) > 3]
        
        if capitalized:
            return " ".join(capitalized[:3])
        else:
            return f"Unknown Threat {datetime.now().strftime('%Y%m%d')}"

    def _extract_platforms(self, description: str) -> List[str]:
        """Extract platforms from description."""
        platforms = []
        platform_keywords = {
            "windows": ["windows", "win32", "exe", "dll", "registry"],
            "linux": ["linux", "unix", "bash", "elf"],
            "macos": ["mac", "macos", "osx", "darwin"],
            "android": ["android", "apk"],
            "ios": ["ios", "iphone", "ipad"]
        }
        
        desc_lower = description.lower()
        for platform, keywords in platform_keywords.items():
            if any(keyword in desc_lower for keyword in keywords):
                platforms.append(platform)
        
        return platforms if platforms else ["unknown"]

    def _assess_severity(self, description: str) -> str:
        """Assess severity based on description."""
        desc_lower = description.lower()
        
        critical_indicators = ["remote code execution", "privilege escalation", 
                             "data exfiltration", "ransomware", "worm"]
        high_indicators = ["exploit", "vulnerability", "backdoor", "trojan"]
        medium_indicators = ["suspicious", "anomalous", "unusual"]
        
        if any(indicator in desc_lower for indicator in critical_indicators):
            return "critical"
        elif any(indicator in desc_lower for indicator in high_indicators):
            return "high"
        elif any(indicator in desc_lower for indicator in medium_indicators):
            return "medium"
        else:
            return "low"

    def get_custom_technique(self, technique_id: str) -> Optional[CustomTechnique]:
        """Get a custom technique by ID."""
        return self.custom_techniques.get(technique_id)

    def get_procedural_cluster(self, cluster_id: str) -> Optional[ProceduralCluster]:
        """Get a procedural cluster by ID."""
        return self.procedural_clusters.get(cluster_id)

    def search_custom_techniques(self, query: str, category: Optional[str] = None) -> List[CustomTechnique]:
        """Search custom techniques by query and category."""
        results = []
        query_lower = query.lower()
        
        for technique in self.custom_techniques.values():
            # Check if query matches name, description, or tags
            tags_match = (technique.tags and 
                         any(query_lower in tag.lower() for tag in technique.tags))
            
            if (query_lower in technique.name.lower() or 
                query_lower in technique.description.lower() or
                tags_match):
                
                # Filter by category if specified
                if category is None or technique.category == category:
                    results.append(technique)
        
        return results

    def get_all_categories(self) -> List[str]:
        """Get all custom technique categories."""
        return list(set(tech.category for tech in self.custom_techniques.values()))

    def get_techniques_by_category(self, category: str) -> List[CustomTechnique]:
        """Get all techniques in a specific category."""
        return [tech for tech in self.custom_techniques.values() 
                if tech.category == category]

    def export_to_elasticsearch_format(self) -> List[Dict]:
        """Export custom techniques in a format suitable for Elasticsearch."""
        es_docs = []
        
        # Export custom techniques
        for tech_id, technique in self.custom_techniques.items():
            doc = {
                "id": tech_id,
                "type": "custom_technique",
                "name": technique.name,
                "description": technique.description,
                "category": technique.category,
                "subcategory": technique.subcategory,
                "platforms": technique.platforms,
                "severity": technique.severity,
                "detection_difficulty": technique.detection_difficulty,
                "sources": technique.sources,
                "related_mitre_techniques": technique.related_mitre_techniques,
                "tags": technique.tags,
                "created_date": technique.created_date,
                "updated_date": technique.updated_date,
                "metadata": technique.metadata
            }
            es_docs.append(doc)
        
        # Export procedural clusters
        for cluster_id, cluster in self.procedural_clusters.items():
            doc = {
                "id": cluster_id,
                "type": "procedural_cluster",
                "name": cluster.name,
                "description": cluster.description,
                "procedures": cluster.procedures,
                "centroid_procedure": cluster.centroid_procedure,
                "cluster_size": cluster.cluster_size,
                "coherence_score": cluster.coherence_score,
                "related_techniques": cluster.related_techniques,
                "created_date": cluster.created_date,
                "metadata": cluster.metadata
            }
            es_docs.append(doc)
        
        return es_docs

    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive statistics about custom techniques and clusters."""
        # Initialize stats structure
        stats = {
            "total_custom_techniques": len(self.custom_techniques),
            "total_procedural_clusters": len(self.procedural_clusters),
            "techniques_by_category": {},
            "techniques_by_severity": {},
            "techniques_by_platform": {},
            "clusters_by_size": {},
            "clusters_by_coherence": {},
            "average_cluster_coherence": 0.0,
            "top_techniques_by_category": {},
            "cluster_analysis": {}
        }
        
        # Calculate technique statistics by querying actual data
        for technique in self.custom_techniques.values():
            # Category distribution
            category = technique.category
            stats["techniques_by_category"][category] = stats["techniques_by_category"].get(category, 0) + 1
            
            # Severity distribution
            severity = technique.severity
            stats["techniques_by_severity"][severity] = stats["techniques_by_severity"].get(severity, 0) + 1
            
            # Platform distribution
            if technique.platforms:  # Check if platforms is not None
                for platform in technique.platforms:
                    stats["techniques_by_platform"][platform] = stats["techniques_by_platform"].get(platform, 0) + 1
        
        # Calculate cluster statistics by analyzing actual cluster data
        if self.procedural_clusters:
            coherence_scores = []
            cluster_sizes = []
            
            for cluster in self.procedural_clusters.values():
                coherence_scores.append(cluster.coherence_score)
                cluster_sizes.append(cluster.cluster_size)
                
                # Cluster size distribution (more granular grouping)
                if cluster.cluster_size <= 2:
                    size_group = "small (1-2)"
                elif cluster.cluster_size <= 5:
                    size_group = "medium (3-5)"
                elif cluster.cluster_size <= 10:
                    size_group = "large (6-10)"
                else:
                    size_group = "very_large (10+)"
                
                stats["clusters_by_size"][size_group] = stats["clusters_by_size"].get(size_group, 0) + 1
                
                # Coherence distribution
                if cluster.coherence_score >= 0.8:
                    coherence_group = "high (0.8+)"
                elif cluster.coherence_score >= 0.6:
                    coherence_group = "medium (0.6-0.8)"
                elif cluster.coherence_score >= 0.4:
                    coherence_group = "low (0.4-0.6)"
                else:
                    coherence_group = "very_low (<0.4)"
                
                stats["clusters_by_coherence"][coherence_group] = stats["clusters_by_coherence"].get(coherence_group, 0) + 1
            
            # Calculate average coherence
            stats["average_cluster_coherence"] = sum(coherence_scores) / len(coherence_scores)
            
            # Advanced cluster analysis
            stats["cluster_analysis"] = {
                "min_coherence": min(coherence_scores) if coherence_scores else 0.0,
                "max_coherence": max(coherence_scores) if coherence_scores else 0.0,
                "median_cluster_size": sorted(cluster_sizes)[len(cluster_sizes)//2] if cluster_sizes else 0,
                "total_procedures": sum(cluster_sizes),
                "clusters_with_high_coherence": len([c for c in coherence_scores if c >= 0.7]),
                "clusters_needing_refinement": len([c for c in coherence_scores if c < 0.5])
            }
        
        # Get top techniques per category (most recent or highest priority)
        for category in stats["techniques_by_category"].keys():
            category_techniques = [t for t in self.custom_techniques.values() if t.category == category]
            # Sort by creation date (most recent first), handle None values
            category_techniques.sort(key=lambda x: x.created_date or "", reverse=True)
            stats["top_techniques_by_category"][category] = [
                {"id": t.id, "name": t.name, "severity": t.severity} 
                for t in category_techniques[:3]  # Top 3 most recent
            ]
        
        return stats

    def get_cluster_insights(self) -> Dict[str, Any]:
        """Get detailed insights about procedural clusters."""
        if not self.procedural_clusters:
            return {"message": "No procedural clusters available for analysis"}
        
        insights = {
            "cluster_quality_distribution": {},
            "procedure_patterns": {},
            "improvement_suggestions": [],
            "cluster_relationships": {}
        }
        
        # Analyze cluster quality
        high_quality_clusters = []
        low_quality_clusters = []
        
        for cluster_id, cluster in self.procedural_clusters.items():
            if cluster.coherence_score >= 0.7:
                high_quality_clusters.append({
                    "id": cluster_id,
                    "name": cluster.name,
                    "coherence": cluster.coherence_score,
                    "size": cluster.cluster_size
                })
            elif cluster.coherence_score < 0.5:
                low_quality_clusters.append({
                    "id": cluster_id,
                    "name": cluster.name,
                    "coherence": cluster.coherence_score,
                    "size": cluster.cluster_size
                })
        
        insights["cluster_quality_distribution"] = {
            "high_quality_clusters": high_quality_clusters,
            "low_quality_clusters": low_quality_clusters,
            "total_clusters": len(self.procedural_clusters)
        }
        
        # Suggest improvements
        if low_quality_clusters:
            insights["improvement_suggestions"].append(
                f"Consider refining {len(low_quality_clusters)} clusters with low coherence scores"
            )
        
        if len(self.procedural_clusters) < 5:
            insights["improvement_suggestions"].append(
                "Consider adding more procedural clusters to improve analysis coverage"
            )
        
        # Find common procedure patterns
        all_procedures = []
        for cluster in self.procedural_clusters.values():
            all_procedures.extend(cluster.procedures)
        
        # Simple pattern detection (can be enhanced with NLP)
        common_terms = {}
        for procedure in all_procedures:
            words = procedure.lower().split()
            for word in words:
                if len(word) > 4:  # Focus on meaningful words
                    common_terms[word] = common_terms.get(word, 0) + 1
        
        # Get top patterns
        top_patterns = sorted(common_terms.items(), key=lambda x: x[1], reverse=True)[:10]
        insights["procedure_patterns"]["common_terms"] = top_patterns
        
        return insights

    def get_clustering_recommendations(self) -> List[str]:
        """Get recommendations for improving clustering."""
        recommendations = []
        
        stats = self.get_stats()
        
        # Check cluster distribution
        if stats["total_procedural_clusters"] == 0:
            recommendations.append("Create initial procedural clusters from threat intelligence or attack documentation")
        elif stats["total_procedural_clusters"] < 3:
            recommendations.append("Add more procedural clusters to improve analytical coverage")
        
        # Check coherence
        if "cluster_analysis" in stats:
            analysis = stats["cluster_analysis"]
            if analysis.get("clusters_needing_refinement", 0) > 0:
                recommendations.append(f"Refine {analysis['clusters_needing_refinement']} clusters with low coherence scores")
            
            if analysis.get("average_cluster_coherence", 0) < 0.6:
                recommendations.append("Overall cluster quality is low - consider reviewing procedure groupings")
        
        # Check technique coverage
        if stats["total_custom_techniques"] > stats["total_procedural_clusters"] * 3:
            recommendations.append("Consider creating more clusters to better organize the growing technique collection")
        
        return recommendations


# Example usage functions for procedural clustering
def create_example_clusters():
    """Create example procedural clusters for demonstration."""
    manager = CustomTechniqueManager()
    
    # Example 1 - Memory Injection Techniques
    memory_injection_text = """
    The payload decompresses executable code in memory using standard compression algorithms.
    It then injects the code into target processes using process hollowing techniques.
    The injected code operates within legitimate process contexts to maintain stealth and persistence.
    """
    
    # Example 2 - Data Collection Procedures
    data_collection_text = """
    The system enumerates network configurations and installed software packages.
    It compiles comprehensive system information including running processes and services.
    The collected data is prepared for exfiltration through encrypted communication channels.
    """
    
    # Create clusters
    memory_cluster_id = manager.create_procedural_cluster_from_text(
        memory_injection_text, "Memory Injection Procedures"
    )
    
    data_cluster_id = manager.create_procedural_cluster_from_text(
        data_collection_text, "Data Collection Procedures"
    )
    
    print(f"Created memory injection cluster: {memory_cluster_id}")
    print(f"Created data collection cluster: {data_cluster_id}")
    
    return manager


if __name__ == "__main__":
    # Example usage
    manager = create_example_clusters()
    print("\nCustom Techniques Stats:")
    print(json.dumps(manager.get_stats(), indent=2))
