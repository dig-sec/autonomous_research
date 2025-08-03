"""
Research Summary Manager

Manages research summaries and caching for techniques.
"""

import json
import os
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class ResearchSummary:
    """Structured research summary for a technique."""
    
    technique_id: str
    platform: str
    summary: str
    sources: List[str]
    confidence_score: float
    last_updated: datetime
    source_count: int
    research_depth: str = "basic"
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data["last_updated"] = self.last_updated.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> "ResearchSummary":
        """Create from dictionary."""
        data["last_updated"] = datetime.fromisoformat(data["last_updated"])
        return cls(**data)


class ResearchSummaryManager:
    """Manages research summaries with intelligent caching and reuse."""

    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.cache_dir = self.project_root / "cache" / "research_summaries"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.summaries_file = self.cache_dir / "research_cache.json"
        self._summaries_cache = self._load_summaries()

    def _load_summaries(self) -> Dict[str, ResearchSummary]:
        """Load all cached research summaries."""
        if not self.summaries_file.exists():
            return {}
        
        try:
            with open(self.summaries_file, "r") as f:
                data = json.load(f)
            
            summaries = {}
            for key, summary_data in data.items():
                summaries[key] = ResearchSummary.from_dict(summary_data)
            
            return summaries
        except Exception as e:
            print(f"Error loading research summaries: {e}")
            return {}

    def _save_summaries(self):
        """Save all summaries to cache file."""
        data = {}
        for key, summary in self._summaries_cache.items():
            data[key] = summary.to_dict()
        
        with open(self.summaries_file, "w") as f:
            json.dump(data, f, indent=2)

    def _get_cache_key(self, technique_id: str, platform: str) -> str:
        """Generate cache key for a technique and platform."""
        return f"{technique_id}_{platform.lower()}"

    def get_summary(self, technique_id: str, platform: str) -> Optional[ResearchSummary]:
        """Get research summary for a technique."""
        cache_key = self._get_cache_key(technique_id, platform)
        return self._summaries_cache.get(cache_key)

    def update_summary(
        self, 
        technique_id: str, 
        platform: str, 
        research_contexts: List[str], 
        sources: List[str]
    ) -> ResearchSummary:
        """Create or update research summary."""
        
        # Combine research contexts
        combined_summary = self._combine_research_contexts(research_contexts)
        
        # Calculate confidence score
        confidence = self._calculate_confidence_score(research_contexts, sources)
        
        # Create summary
        summary = ResearchSummary(
            technique_id=technique_id,
            platform=platform,
            summary=combined_summary,
            sources=sources[:20],  # Limit sources
            confidence_score=confidence,
            last_updated=datetime.now(),
            source_count=len(sources),
            research_depth="comprehensive" if len(research_contexts) > 2 else "basic"
        )
        
        # Cache the summary
        cache_key = self._get_cache_key(technique_id, platform)
        self._summaries_cache[cache_key] = summary
        self._save_summaries()
        
        return summary

    def _combine_research_contexts(self, contexts: List[str]) -> str:
        """Combine multiple research contexts into a coherent summary."""
        if not contexts:
            return ""
        
        if len(contexts) == 1:
            return contexts[0]
        
        # Simple combination for now - could be enhanced with LLM summarization
        combined = "COMPREHENSIVE RESEARCH SUMMARY:\n\n"
        
        for i, context in enumerate(contexts, 1):
            combined += f"Research Source {i}:\n{context}\n\n"
        
        return combined

    def _calculate_confidence_score(self, contexts: List[str], sources: List[str]) -> float:
        """Calculate confidence score based on research quality."""
        base_score = 5.0
        
        # Add points for multiple contexts
        context_score = min(len(contexts) * 1.5, 3.0)
        
        # Add points for multiple sources
        source_score = min(len(sources) * 0.2, 1.5)
        
        # Add points for content quality indicators
        quality_score = 0.0
        for context in contexts:
            if len(context) > 1000:
                quality_score += 0.3
            if "mitre" in context.lower():
                quality_score += 0.2
            if any(indicator in context.lower() for indicator in ["github", "cve", "detection", "mitigation"]):
                quality_score += 0.1
        
        quality_score = min(quality_score, 1.0)
        
        total_score = base_score + context_score + source_score + quality_score
        return min(total_score, 10.0)

    def get_summary_for_generation(self, technique_id: str, platform: str, file_type: str) -> str:
        """Get formatted summary for content generation."""
        summary = self.get_summary(technique_id, platform)
        if not summary:
            return ""
        
        formatted = f"""RESEARCH CONTEXT (Confidence: {summary.confidence_score:.1f}/10):

{summary.summary}

SOURCES: {', '.join(summary.sources[:5])}
RESEARCH DEPTH: {summary.research_depth.title()}
LAST UPDATED: {summary.last_updated.strftime('%Y-%m-%d')}
"""
        return formatted

    def get_all_summaries(self) -> List[ResearchSummary]:
        """Get all cached research summaries."""
        return list(self._summaries_cache.values())

    def clear_cache(self):
        """Clear all cached summaries."""
        self._summaries_cache.clear()
        if self.summaries_file.exists():
            self.summaries_file.unlink()

    def get_cache_stats(self) -> Dict:
        """Get cache statistics."""
        summaries = list(self._summaries_cache.values())
        
        if not summaries:
            return {"total": 0}
        
        avg_confidence = sum(s.confidence_score for s in summaries) / len(summaries)
        
        return {
            "total": len(summaries),
            "avg_confidence": round(avg_confidence, 2),
            "high_confidence": len([s for s in summaries if s.confidence_score >= 8.0]),
            "low_confidence": len([s for s in summaries if s.confidence_score < 6.0]),
            "platforms": list(set(s.platform for s in summaries)),
        }
