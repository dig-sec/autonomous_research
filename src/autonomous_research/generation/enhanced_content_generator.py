"""
Enhanced Content Generator for JSON-based Output

Generates research content and stores it as structured JSON objects in Elasticsearch
instead of individual markdown files.
"""

import os
import requests
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Callable
import time
import logging

from autonomous_research.output.elasticsearch_output_manager import (
    ResearchOutput, ElasticsearchOutputManager, create_unified_research_output
)


class EnhancedContentGenerator:
    """
    Enhanced content generator that creates unified JSON research outputs.
    Replaces file-based content generation with Elasticsearch storage.
    """

    def __init__(self, model: str = "llama2-uncensored:7b"):
        self.model = model
        self.ollama_url = os.getenv("OLLAMA_HOST", "http://localhost:11434/api/generate")
        self.logger = logging.getLogger(__name__)
        
        # Initialize output manager
        self.output_manager = ElasticsearchOutputManager()
        
        # Content sections to generate
        self.content_sections = [
            "description",
            "detection", 
            "mitigation",
            "purple_playbook",
            "references",
            "agent_notes"
        ]

    def generate_unified_research_output(
        self,
        technique: Dict,
        research_context: str,
        sources: Optional[List[str]] = None,
        confidence_score: float = 0.0,
        shutdown_flag: Optional[Callable] = None
    ) -> Optional[ResearchOutput]:
        """
        Generate a complete research output as a unified JSON object.
        
        Args:
            technique: Technique dictionary with id, name, platform info
            research_context: Research context string
            sources: List of research sources
            confidence_score: Research confidence score
            shutdown_flag: Optional shutdown check function
            
        Returns:
            ResearchOutput object if successful, None otherwise
        """
        technique_id = technique["id"]
        technique_name = technique.get("name", technique_id)
        platform = technique.get("platform", "unknown")
        
        self.logger.info(f"Generating unified research output for {technique_id}")
        
        # Check for existing output
        existing_output = self.output_manager.get_research_output(technique_id, platform)
        if existing_output and self._is_output_current(existing_output):
            self.logger.info(f"Using existing research output for {technique_id}")
            return existing_output
        
        # Generate all content sections
        content_sections = {}
        generation_success = True
        
        for section in self.content_sections:
            if shutdown_flag and shutdown_flag():
                self.logger.info("Shutdown requested during content generation")
                return None
                
            self.logger.info(f"Generating {section} for {technique_id}")
            content = self._generate_section_content(
                technique, research_context, section
            )
            
            if content and self._validate_content_quality(content, section):
                content_sections[section] = content
                self.logger.info(f"✅ Generated {section} ({len(content.split())} words)")
            else:
                self.logger.warning(f"⚠️ Failed to generate quality {section} content")
                content_sections[section] = ""
                generation_success = False
        
        if shutdown_flag and shutdown_flag():
            self.logger.info("Shutdown requested after content generation")
            return None
        
        # Create unified research output
        research_output = create_unified_research_output(
            technique=technique,
            research_context=research_context,
            content_sections=content_sections,
            sources=sources or [],
            confidence_score=confidence_score
        )
        
        # Enhance with additional metadata
        research_output.category = technique.get("category", "technique")
        research_output.tags = self._extract_tags(technique, content_sections)
        research_output.related_techniques = self._find_related_techniques(content_sections)
        
        # Store in Elasticsearch
        if self.output_manager.store_research_output(research_output):
            self.logger.info(f"✅ Stored unified research output for {technique_id}")
            return research_output
        else:
            self.logger.error(f"❌ Failed to store research output for {technique_id}")
            return None

    def update_research_section(
        self,
        technique_id: str,
        platform: str,
        section: str,
        new_content: Optional[str] = None,
        regenerate: bool = False
    ) -> bool:
        """
        Update a specific section of existing research output.
        
        Args:
            technique_id: Technique identifier
            platform: Platform identifier
            section: Section name to update
            new_content: New content (if not provided, will regenerate)
            regenerate: Force regeneration of content
            
        Returns:
            Success status
        """
        if not new_content and not regenerate:
            self.logger.error("Must provide new_content or set regenerate=True")
            return False
        
        # Get existing output
        existing_output = self.output_manager.get_research_output(technique_id, platform)
        if not existing_output:
            self.logger.error(f"No existing research output found for {technique_id}_{platform}")
            return False
        
        # Generate new content if needed
        if regenerate and not new_content:
            technique = {
                "id": technique_id,
                "name": existing_output.technique_name,
                "platform": platform
            }
            new_content = self._generate_section_content(
                technique, existing_output.research_context, section
            )
            
            if not new_content:
                self.logger.error(f"Failed to regenerate {section} content")
                return False
        
        # Update section
        success = self.output_manager.update_research_section(
            technique_id, platform, section, new_content or ""
        )
        
        if success:
            self.logger.info(f"✅ Updated {section} for {technique_id}_{platform}")
        else:
            self.logger.error(f"❌ Failed to update {section} for {technique_id}_{platform}")
        
        return success

    def _generate_section_content(
        self, 
        technique: Dict, 
        research_context: str, 
        section: str
    ) -> Optional[str]:
        """Generate content for a specific section using LLM."""
        
        prompt = self._get_section_prompt(technique, research_context, section)
        
        try:
            # Generate using Ollama
            response = requests.post(
                self.ollama_url,
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "top_p": 0.9,
                        "max_tokens": 2000
                    }
                },
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result.get("response", "").strip()
                
                # Post-process content
                return self._post_process_content(content, section)
            else:
                self.logger.error(f"Ollama request failed: {response.status_code}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error generating {section} content: {e}")
            return None

    def _get_section_prompt(self, technique: Dict, research_context: str, section: str) -> str:
        """Get the prompt for generating a specific section."""
        
        technique_id = technique["id"]
        technique_name = technique.get("name", "Unknown Technique")
        platform = technique.get("platform", "Windows")
        
        base_context = f"""
Technique: {technique_id} - {technique_name}
Platform: {platform}

Research Context:
{research_context}

Generate professional, technical content for the {section} section.
"""
        
        section_prompts = {
            "description": f"""{base_context}

Create a comprehensive technical description including:
- Overview of the technique and its purpose
- Technical implementation details
- How attackers typically use this technique
- Prerequisites and requirements
- Common variations and methods
- Impact and consequences for defenders

Format as clear, structured text with technical depth.""",

            "detection": f"""{base_context}

Create detailed detection guidance including:
- Key indicators and observables (IOCs, IOAs)
- Log sources and data requirements
- Detection rules and signatures (SIEM, EDR)
- Monitoring strategies and hunt queries
- Behavioral indicators and anomalies
- False positive considerations
- Detection confidence levels

Include specific technical detection methods and tools.""",

            "mitigation": f"""{base_context}

Create comprehensive mitigation strategies including:
- Preventive security controls
- Detective controls and monitoring
- Response and containment procedures
- Configuration hardening recommendations
- Security best practices and policies
- Compensating controls
- Implementation priorities

Focus on actionable, implementable mitigations.""",

            "purple_playbook": f"""{base_context}

Create a purple team playbook including:
- Attack simulation steps and procedures
- Detection validation methods
- Response testing scenarios
- Exercise objectives and success criteria
- Tools and techniques for simulation
- Metrics and measurement approaches
- Lessons learned integration

Provide actionable purple team exercises.""",

            "references": f"""{base_context}

Compile comprehensive references including:
- MITRE ATT&CK technique mappings
- CVE references and vulnerability databases
- Security research papers and whitepapers
- Vendor documentation and advisories
- Tool documentation and resources
- Real-world attack examples
- Additional reading materials

Format as a structured reference list.""",

            "agent_notes": f"""{base_context}

Create analytical agent notes including:
- Research methodology and approach
- Data quality assessment
- Confidence levels and limitations
- Gaps in available information
- Recommendations for further research
- Correlation with other techniques
- Analysis insights and observations

Provide meta-analysis of the research process."""
        }
        
        return section_prompts.get(section, base_context)

    def _post_process_content(self, content: str, section: str) -> str:
        """Post-process generated content for consistency and quality."""
        if not content:
            return ""
        
        # Remove any AI-generated disclaimers or meta-comments
        lines = content.split('\n')
        filtered_lines = []
        
        for line in lines:
            line = line.strip()
            if line and not any(phrase in line.lower() for phrase in [
                "i am an ai", "as an ai", "i cannot", "i don't have access",
                "please note", "disclaimer", "this is generated"
            ]):
                filtered_lines.append(line)
        
        processed_content = '\n'.join(filtered_lines)
        
        # Add section-specific formatting
        if section in ["detection", "mitigation"] and processed_content:
            # Ensure these sections have actionable content
            if len(processed_content.split()) < 50:
                processed_content += "\n\n*Additional research and validation recommended for comprehensive coverage.*"
        
        return processed_content.strip()

    def _validate_content_quality(self, content: str, section: str) -> bool:
        """Validate the quality of generated content."""
        if not content or len(content.strip()) < 50:
            return False
        
        word_count = len(content.split())
        
        # Section-specific quality thresholds
        min_words = {
            "description": 100,
            "detection": 75,
            "mitigation": 75,
            "purple_playbook": 100,
            "references": 50,
            "agent_notes": 50
        }
        
        required_words = min_words.get(section, 50)
        
        if word_count < required_words:
            self.logger.warning(f"{section} content too short: {word_count} words")
            return False
        
        # Check for meaningful content (not just filler)
        meaningful_indicators = [
            "technique", "attack", "detection", "mitigation", "security",
            "system", "process", "network", "file", "registry"
        ]
        
        content_lower = content.lower()
        meaningful_count = sum(1 for indicator in meaningful_indicators if indicator in content_lower)
        
        if meaningful_count < 3:
            self.logger.warning(f"{section} content lacks technical depth")
            return False
        
        return True

    def _extract_tags(self, technique: Dict, content_sections: Dict[str, str]) -> List[str]:
        """Extract relevant tags from technique data and content."""
        tags = []
        
        # Add platform tag
        platform = technique.get("platform", "unknown")
        if platform != "unknown":
            tags.append(platform.lower())
        
        # Add category tag
        category = technique.get("category", "")
        if category:
            tags.append(category.lower())
        
        # Extract tags from content based on common security terms
        all_content = " ".join(content_sections.values()).lower()
        
        tag_keywords = {
            "persistence": ["persistence", "startup", "registry", "scheduled"],
            "privilege_escalation": ["elevation", "privilege", "admin", "root"],
            "lateral_movement": ["lateral", "remote", "ssh", "rdp", "smb"],
            "execution": ["execute", "payload", "shell", "command"],
            "discovery": ["enumerate", "scan", "reconnaissance", "discovery"],
            "collection": ["collect", "gather", "harvest", "steal"],
            "exfiltration": ["exfiltrate", "transfer", "upload", "download"],
            "defense_evasion": ["evasion", "bypass", "hide", "obfuscate"],
            "credential_access": ["credential", "password", "hash", "token"],
            "impact": ["damage", "disrupt", "destroy", "ransom"]
        }
        
        for tag, keywords in tag_keywords.items():
            if any(keyword in all_content for keyword in keywords):
                tags.append(tag)
        
        return list(set(tags))  # Remove duplicates

    def _find_related_techniques(self, content_sections: Dict[str, str]) -> List[str]:
        """Find related techniques mentioned in the content."""
        related = []
        all_content = " ".join(content_sections.values())
        
        # Look for MITRE technique references (T1xxx format)
        import re
        technique_pattern = r'T\d{4}(?:\.\d{3})?'
        matches = re.findall(technique_pattern, all_content)
        
        for match in matches:
            if match not in related:
                related.append(match)
        
        return related[:10]  # Limit to 10 related techniques

    def _is_output_current(self, output: ResearchOutput) -> bool:
        """Check if existing output is current and doesn't need regeneration."""
        from datetime import datetime, timezone, timedelta
        
        # Check age (regenerate if older than 30 days)
        try:
            last_updated = datetime.fromisoformat(output.last_updated.replace('Z', '+00:00'))
            age = datetime.now(timezone.utc) - last_updated
            if age > timedelta(days=30):
                return False
        except:
            return False
        
        # Check quality score (regenerate if low quality)
        if output.quality_score < 0.6:
            return False
        
        # Check completeness (regenerate if incomplete)
        if output.completeness_score < 0.7:
            return False
        
        return True

    def get_generation_stats(self) -> Dict:
        """Get statistics about content generation."""
        if not self.output_manager.es:
            return {"error": "Elasticsearch not available"}
        
        return self.output_manager.get_analytics_summary()

    def batch_regenerate_low_quality(self, min_quality_score: float = 0.6) -> int:
        """Regenerate all outputs with quality scores below threshold."""
        low_quality_outputs = self.output_manager.search_research_outputs(
            min_quality_score=0.0,  # Get all outputs
            limit=1000
        )
        
        regenerated_count = 0
        
        for output in low_quality_outputs:
            if output.quality_score < min_quality_score:
                technique = {
                    "id": output.technique_id,
                    "name": output.technique_name,
                    "platform": output.platform
                }
                
                new_output = self.generate_unified_research_output(
                    technique=technique,
                    research_context=output.research_context,
                    sources=output.sources or [],
                    confidence_score=output.confidence_score
                )
                
                if new_output:
                    regenerated_count += 1
                    self.logger.info(f"Regenerated low-quality output: {output.technique_id}")
        
        return regenerated_count


# Backwards compatibility for existing code
class ContentGenerator(EnhancedContentGenerator):
    """
    Backwards compatible wrapper that maintains file-based interface
    while internally using the new JSON-based system.
    """
    
    def generate_technique_content(
        self,
        technique: Dict,
        research_context: str,
        output_dir: Path,
        shutdown_flag: Optional[Callable] = None
    ) -> int:
        """
        Legacy interface for file-based content generation.
        Now generates JSON output in Elasticsearch instead of files.
        """
        # Generate unified output
        research_output = self.generate_unified_research_output(
            technique=technique,
            research_context=research_context,
            shutdown_flag=shutdown_flag
        )
        
        if research_output:
            self.logger.info(f"Generated unified research output for {technique['id']} (legacy interface)")
            return len(self.content_sections)  # Return count of sections generated
        else:
            return 0
