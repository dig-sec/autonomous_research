"""
Content Generator

Handles content generation using local LLM with quality validation.
"""

import os
import requests
import json
from pathlib import Path
from typing import Dict, List, Optional
import time


class ContentGenerator:
    """Generates content using local Ollama LLM."""

    def __init__(self, model: str = "llama2-uncensored:7b"):
        self.model = model
        self.ollama_url = os.getenv("OLLAMA_HOST", "http://localhost:11434/api/generate")
        
        # Content templates
        self.template_files = [
            "description.md",
            "detection.md", 
            "mitigation.md",
            "purple_playbook.md",
            "references.md",
            "agent_notes.md"
        ]

    def generate_technique_content(
        self,
        technique: Dict,
        research_context: str,
        output_dir: Path,
        shutdown_flag: callable = None
    ) -> int:
        """Generate all content files for a technique, with shutdown checks."""
        output_dir.mkdir(parents=True, exist_ok=True)
        generated_count = 0
        for file_name in self.template_files:
            if shutdown_flag and shutdown_flag():
                print("Shutdown requested during content generation loop, aborting.")
                break
            file_path = output_dir / file_name
            # Generate content for this file
            content = self._generate_file_content(
                technique, research_context, file_name
            )
            if shutdown_flag and shutdown_flag():
                print("Shutdown requested after file generation, aborting.")
                break
            if content and self._validate_content_quality(content):
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
                generated_count += 1
                print(f"Generated {file_name} for {technique['id']}")
            else:
                print(f"Failed to generate quality content for {file_name}")
        return generated_count

    def _generate_file_content(
        self, 
        technique: Dict, 
        research_context: str, 
        file_name: str
    ) -> Optional[str]:
        """Generate content for a specific file."""
        
        prompt = self._get_file_prompt(technique, research_context, file_name)
        
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
                return result.get("response", "").strip()
            else:
                print(f"Ollama request failed: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"Error generating content: {e}")
            return None

    def _get_file_prompt(self, technique: Dict, research_context: str, file_name: str) -> str:
        """Get the prompt for generating a specific file."""
        
        technique_id = technique["id"]
        technique_name = technique.get("name", "Unknown Technique")
        platform = technique.get("platform", "Windows")
        
        base_context = f"""
Technique: {technique_id} - {technique_name}
Platform: {platform}

Research Context:
{research_context}

Generate professional, technical content for: {file_name}
"""
        
        if file_name == "description.md":
            return f"""{base_context}

Create a comprehensive technical description including:
- Overview of the technique
- How it works technically
- Common implementations
- Prerequisites and requirements
- Impact and consequences

Format as Markdown with clear sections and technical details."""

        elif file_name == "detection.md":
            return f"""{base_context}

Create detailed detection guidance including:
- Key indicators and observables
- Log sources and data requirements
- Detection rules and signatures
- Monitoring strategies
- False positive considerations

Include specific technical detection methods and tools."""

        elif file_name == "mitigation.md":
            return f"""{base_context}

Create comprehensive mitigation strategies including:
- Preventive controls
- Detective controls
- Response procedures
- Configuration recommendations
- Security best practices

Focus on actionable, implementable mitigations."""

        elif file_name == "purple_playbook.md":
            return f"""{base_context}

Create a purple team playbook including:
- Attack simulation steps
- Detection validation
- Response procedures
- Metrics and success criteria
- Lessons learned integration

Format as step-by-step procedures for security teams."""

        elif file_name == "references.md":
            return f"""{base_context}

Create a comprehensive reference list including:
- Official documentation
- Security research papers
- Tool repositories
- Detection rules
- Industry reports

Organize by category with descriptions."""

        elif file_name == "agent_notes.md":
            return f"""{base_context}

Create technical notes including:
- Implementation variants
- Platform-specific considerations
- Advanced evasion techniques
- Research gaps
- Future developments

Focus on technical depth and accuracy."""

        else:
            return f"{base_context}\n\nGenerate appropriate content for {file_name}."

    def _validate_content_quality(self, content: str) -> bool:
        """Validate content quality using simple heuristics."""
        
        if not content or len(content) < 200:
            return False
        
        # Check for placeholder patterns
        placeholder_patterns = [
            "[To be determined]",
            "[Detailed explanation",
            "[How attackers use",
            "Use a modern, up-to-date antivirus",
            "Keep your software up-to-date"
        ]
        
        for pattern in placeholder_patterns:
            if pattern in content:
                return False
        
        # Check for minimum content structure
        if content.count('\n') < 5:  # Should have multiple lines
            return False
        
        # Check for reasonable word count
        word_count = len(content.split())
        if word_count < 50:
            return False
        
        return True

    def score_content_quality(self, content: str) -> float:
        """Score content quality from 0-10."""
        
        score = 5.0  # Base score
        
        # Length scoring
        word_count = len(content.split())
        if word_count > 200:
            score += 1.0
        elif word_count > 100:
            score += 0.5
        
        # Structure scoring
        line_count = content.count('\n')
        if line_count > 20:
            score += 0.5
        
        # Technical content indicators
        technical_terms = [
            "registry", "process", "memory", "network", "file", 
            "detection", "mitigation", "attack", "payload"
        ]
        
        term_count = sum(1 for term in technical_terms if term.lower() in content.lower())
        score += min(term_count * 0.2, 1.0)
        
        # Markdown formatting
        if "##" in content:
            score += 0.3
        if "```" in content:
            score += 0.2
        
        return min(score, 10.0)
