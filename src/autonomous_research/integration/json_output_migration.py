"""
Integration module for migrating to JSON-based Elasticsearch output system.

This module provides integration between the existing autonomous system
and the new JSON-based output management system.
"""

import logging
from typing import Dict, List, Optional, Any
from pathlib import Path

from autonomous_research.output.elasticsearch_output_manager import (
    ResearchOutput, ElasticsearchOutputManager
)
from autonomous_research.generation.enhanced_content_generator import EnhancedContentGenerator


class OutputSystemMigration:
    """
    Handles migration from file-based output to JSON-based Elasticsearch storage.
    """
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.logger = logging.getLogger(__name__)
        self.output_manager = ElasticsearchOutputManager()
        self.enhanced_generator = EnhancedContentGenerator()
        
    def migrate_existing_outputs(self) -> Dict[str, int]:
        """
        Migrate existing file-based outputs to Elasticsearch JSON format.
        
        Returns:
            Dictionary with migration statistics
        """
        stats = {
            "files_found": 0,
            "techniques_migrated": 0,
            "migration_errors": 0
        }
        
        output_dir = self.project_root / "output"
        if not output_dir.exists():
            self.logger.info("No existing output directory found")
            return stats
        
        # Scan for existing technique outputs
        for platform_dir in output_dir.iterdir():
            if not platform_dir.is_dir() or platform_dir.name in ["cache", "logs"]:
                continue
                
            platform = platform_dir.name
            techniques_dir = platform_dir / "techniques"
            
            if not techniques_dir.exists():
                continue
                
            for technique_dir in techniques_dir.iterdir():
                if not technique_dir.is_dir():
                    continue
                    
                technique_id = technique_dir.name
                
                try:
                    # Read existing markdown files
                    content_sections = {}
                    file_map = {
                        "description.md": "description",
                        "detection.md": "detection",
                        "mitigation.md": "mitigation",
                        "purple_playbook.md": "purple_playbook",
                        "references.md": "references",
                        "agent_notes.md": "agent_notes"
                    }
                    
                    found_files = False
                    for filename, section in file_map.items():
                        file_path = technique_dir / filename
                        if file_path.exists():
                            content_sections[section] = file_path.read_text(encoding='utf-8')
                            found_files = True
                            stats["files_found"] += 1
                    
                    if found_files:
                        # Create research output object
                        research_output = ResearchOutput(
                            technique_id=technique_id,
                            technique_name=technique_id,  # Will be enhanced later
                            platform=platform,
                            category="technique",
                            **content_sections
                        )
                        
                        # Store in Elasticsearch
                        if self.output_manager.store_research_output(research_output):
                            stats["techniques_migrated"] += 1
                            self.logger.info(f"✅ Migrated {technique_id} ({platform})")
                        else:
                            stats["migration_errors"] += 1
                            self.logger.error(f"❌ Failed to migrate {technique_id} ({platform})")
                    
                except Exception as e:
                    stats["migration_errors"] += 1
                    self.logger.error(f"❌ Error migrating {technique_id}: {e}")
        
        self.logger.info(f"Migration complete: {stats['techniques_migrated']} techniques migrated")
        return stats
    
    def create_migration_backup(self) -> bool:
        """Create backup of existing file-based outputs."""
        import shutil
        from datetime import datetime
        
        output_dir = self.project_root / "output"
        if not output_dir.exists():
            return True
        
        backup_dir = self.project_root / "backup" / f"file_outputs_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        try:
            shutil.copytree(output_dir, backup_dir)
            self.logger.info(f"✅ Created backup at {backup_dir}")
            return True
        except Exception as e:
            self.logger.error(f"❌ Failed to create backup: {e}")
            return False
    
    def validate_migration(self) -> Dict[str, Any]:
        """Validate that migration was successful."""
        validation_results = {
            "elasticsearch_outputs": 0,
            "sample_outputs": [],
            "quality_distribution": {},
            "platform_distribution": {},
            "errors": []
        }
        
        try:
            # Get analytics from Elasticsearch
            analytics = self.output_manager.get_analytics_summary()
            validation_results.update(analytics)
            
            # Get sample outputs for validation
            sample_outputs = self.output_manager.search_research_outputs(limit=5)
            validation_results["sample_outputs"] = [
                {
                    "technique_id": output.technique_id,
                    "platform": output.platform,
                    "quality_score": output.quality_score,
                    "completeness_score": output.completeness_score,
                    "word_count": output.word_count
                }
                for output in sample_outputs
            ]
            
        except Exception as e:
            validation_results["errors"].append(str(e))
            self.logger.error(f"❌ Validation error: {e}")
        
        return validation_results


class AutonomousSystemIntegration:
    """
    Integration layer for updating AutonomousResearchSystem to use JSON-based output.
    """
    
    def __init__(self, autonomous_system):
        self.autonomous_system = autonomous_system
        self.logger = logging.getLogger(__name__)
        
        # Replace content generator with enhanced version
        self.autonomous_system.content_generator = EnhancedContentGenerator(
            model=autonomous_system.model
        )
        
        # Add output manager
        self.autonomous_system.output_manager = ElasticsearchOutputManager()
        
        self.logger.info("✅ Integrated JSON-based output system")
    
    def enhanced_generate_content(self, technique: Dict, research_context: str, shutdown_flag=None) -> bool:
        """
        Enhanced content generation using JSON-based output system.
        Replaces the original generate_content method.
        """
        technique_id = technique["id"]
        platform = technique.get("platform", "windows").lower()
        
        self.logger.info(f"Generating JSON-based content for {technique_id}")
        
        # Extract sources from research context if available
        sources = []
        if hasattr(self.autonomous_system, 'research_manager'):
            summary = self.autonomous_system.research_manager.get_summary(technique_id, platform)
            if summary:
                sources = summary.sources
        
        # Generate unified research output
        research_output = self.autonomous_system.content_generator.generate_unified_research_output(
            technique=technique,
            research_context=research_context,
            sources=sources,
            confidence_score=7.5,  # Default confidence
            shutdown_flag=shutdown_flag
        )
        
        if research_output:
            self.logger.info(f"✅ Generated JSON-based output for {technique_id}")
            return True
        else:
            self.logger.error(f"❌ Failed to generate JSON-based output for {technique_id}")
            return False
    
    def get_enhanced_system_status(self) -> Dict:
        """Get enhanced system status including JSON output metrics."""
        original_status = self.autonomous_system.get_system_status()
        
        # Add JSON output analytics
        try:
            output_analytics = self.autonomous_system.output_manager.get_analytics_summary()
            original_status["json_outputs"] = output_analytics
        except Exception as e:
            self.logger.warning(f"Could not get output analytics: {e}")
            original_status["json_outputs"] = {"error": str(e)}
        
        return original_status
    
    def search_research_outputs(
        self,
        query: Optional[str] = None,
        platform: Optional[str] = None,
        min_quality: Optional[float] = None
    ) -> List[Dict]:
        """Search research outputs with enhanced capabilities."""
        outputs = self.autonomous_system.output_manager.search_research_outputs(
            query=query,
            platform=platform,
            min_quality_score=min_quality,
            limit=50
        )
        
        # Convert to dictionary format for API responses
        return [
            {
                "technique_id": output.technique_id,
                "technique_name": output.technique_name,
                "platform": output.platform,
                "quality_score": output.quality_score,
                "completeness_score": output.completeness_score,
                "word_count": output.word_count,
                "last_updated": output.last_updated,
                "has_detection": bool(output.detection.strip()),
                "has_mitigation": bool(output.mitigation.strip()),
                "tags": output.tags or []
            }
            for output in outputs
        ]


def integrate_json_output_system(autonomous_system, project_root: Path) -> AutonomousSystemIntegration:
    """
    Main integration function to upgrade an existing AutonomousResearchSystem
    to use the new JSON-based output system.
    
    Args:
        autonomous_system: Existing AutonomousResearchSystem instance
        project_root: Project root path
        
    Returns:
        AutonomousSystemIntegration instance
    """
    logger = logging.getLogger(__name__)
    
    # Perform migration if needed
    migration = OutputSystemMigration(project_root)
    
    # Create backup of existing outputs
    logger.info("Creating backup of existing file-based outputs...")
    migration.create_migration_backup()
    
    # Migrate existing outputs to Elasticsearch
    logger.info("Migrating existing outputs to JSON format...")
    migration_stats = migration.migrate_existing_outputs()
    logger.info(f"Migration complete: {migration_stats}")
    
    # Integrate with autonomous system
    integration = AutonomousSystemIntegration(autonomous_system)
    
    # Replace the generate_content method
    autonomous_system.generate_content = integration.enhanced_generate_content
    
    # Validate migration
    logger.info("Validating migration...")
    validation_results = migration.validate_migration()
    logger.info(f"Validation results: {validation_results}")
    
    logger.info("✅ JSON-based output system integration complete")
    return integration


# CLI command for migration
def run_migration_cli():
    """Command-line interface for running migration."""
    import argparse
    from pathlib import Path
    
    parser = argparse.ArgumentParser(description="Migrate to JSON-based output system")
    parser.add_argument("--project-root", default=".", help="Project root directory")
    parser.add_argument("--backup", action="store_true", help="Create backup only")
    parser.add_argument("--validate", action="store_true", help="Validate migration only")
    
    args = parser.parse_args()
    project_root = Path(args.project_root).resolve()
    
    migration = OutputSystemMigration(project_root)
    
    if args.backup:
        print("Creating backup...")
        migration.create_migration_backup()
        print("✅ Backup complete")
        
    elif args.validate:
        print("Validating migration...")
        results = migration.validate_migration()
        print(f"✅ Validation results: {results}")
        
    else:
        print("Running full migration...")
        migration.create_migration_backup()
        stats = migration.migrate_existing_outputs()
        validation = migration.validate_migration()
        
        print(f"✅ Migration complete:")
        print(f"   - Files migrated: {stats['techniques_migrated']}")
        print(f"   - Errors: {stats['migration_errors']}")
        print(f"   - Elasticsearch outputs: {validation.get('total_outputs', 0)}")


if __name__ == "__main__":
    run_migration_cli()
