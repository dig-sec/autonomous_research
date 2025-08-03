"""
Autonomous Research System

A comprehensive system for autonomous security research, technique analysis,
and documentation generation with AI-driven content creation.
"""

__version__ = "2.0.0"
__author__ = "Security Research Team"

# Core imports (only import what exists)
try:
    from .core.autonomous_system import AutonomousResearchSystem
    from .core.project_manager import ProjectManager
    from .research.summary_manager import ResearchSummaryManager
    from .generation.content_generator import ContentGenerator
    from .knowledge.custom_techniques import CustomTechniqueManager, CustomTechnique, ProceduralCluster
    
    __all__ = [
        "AutonomousResearchSystem",
        "ProjectManager", 
        "ResearchSummaryManager",
        "ContentGenerator",
        "CustomTechniqueManager",
        "CustomTechnique", 
        "ProceduralCluster",
    ]
except ImportError as e:
    # Graceful degradation if modules aren't available
    print(f"Warning: Some modules not available: {e}")
    __all__ = []
