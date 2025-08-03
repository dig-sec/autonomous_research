#!/usr/bin/env python3
"""
Command Line Interface for Autonomous Research System
"""

import argparse
import sys
import os
from pathlib import Path

from .core.autonomous_system import AutonomousResearchSystem
from .core.project_manager import ProjectManager


def cmd_init(args):
    """Initialize a new project."""
    print("Initializing Autonomous Research System...")
    
    project_manager = ProjectManager(args.project_dir)
    
    # Create sample techniques if none exist
    techniques = project_manager.load_techniques()
    if not techniques:
        sample_techniques = [
            {
                "id": "T1003",
                "name": "OS Credential Dumping",
                "platform": "Windows",
                "status": "pending",
                "description": "Adversaries may attempt to dump credentials to obtain account login and credential material."
            },
            {
                "id": "T1059",
                "name": "Command and Scripting Interpreter",
                "platform": "Windows", 
                "status": "pending",
                "description": "Adversaries may abuse command and script interpreters to execute commands, scripts, or binaries."
            }
        ]
        
        for technique in sample_techniques:
            project_manager.add_technique(technique)
        
        print(f"Added {len(sample_techniques)} sample techniques")
    
    print(f"Project initialized in {args.project_dir}")


def cmd_run(args):
    """Run the autonomous research system."""
    print("Starting Autonomous Research System...")
    
    system = AutonomousResearchSystem(
        project_root=args.project_dir,
        model=args.model,
        update_interval=args.interval
    )
    
    if args.single_cycle:
        print("Running single cycle...")
        stats = system.run_single_cycle()
        print(f"Cycle completed: {stats}")
    else:
        print("Running autonomous mode (Ctrl+C to stop)...")
        system.run_autonomous()


def cmd_generate(args):
    """Generate content for specific techniques."""
    system = AutonomousResearchSystem(
        project_root=args.project_dir,
        model=args.model
    )
    
    if args.technique_id:
        # Generate for specific technique
        project_manager = ProjectManager(args.project_dir)
        techniques = project_manager.load_techniques()
        
        target_technique = None
        for technique in techniques:
            if technique["id"] == args.technique_id:
                target_technique = technique
                break
        
        if target_technique:
            research_context = system.conduct_research(target_technique)
            if research_context:
                success = system.generate_content(target_technique, research_context)
                if success:
                    system.update_technique_status(args.technique_id)
                    print(f"Generated content for {args.technique_id}")
                else:
                    print(f"Failed to generate content for {args.technique_id}")
            else:
                print(f"No research context found for {args.technique_id}")
        else:
            print(f"Technique {args.technique_id} not found")
    else:
        # Generate for all pending techniques
        stats = system.run_single_cycle()
        print(f"Generated content for {stats['content_generated']} techniques")


def cmd_status(args):
    """Show system status."""
    system = AutonomousResearchSystem(project_root=args.project_dir)
    status = system.get_system_status()
    
    print("=== Autonomous Research System Status ===")
    print(f"Total Techniques: {status['total_techniques']}")
    print(f"Completed: {status['completed_techniques']}")
    print(f"Pending: {status['pending_techniques']}")
    print(f"Research Summaries: {status['research_summaries']}")
    print(f"Last Updated: {status.get('last_updated', 'Never')}")
    print(f"System Version: {status['system_version']}")
    
    # Show project stats
    project_manager = ProjectManager(args.project_dir)
    project_stats = project_manager.get_project_stats()
    
    print("\n=== Project Statistics ===")
    print(f"By Platform: {project_stats['by_platform']}")
    print(f"By Status: {project_stats['by_status']}")
    print(f"By Type: {project_stats['by_type']}")


def cmd_add_technique(args):
    """Add a new technique."""
    project_manager = ProjectManager(args.project_dir)
    
    technique = {
        "id": args.technique_id,
        "name": args.name,
        "platform": args.platform,
        "status": "pending",
        "description": args.description or f"Technique {args.technique_id}"
    }
    
    if project_manager.add_technique(technique):
        print(f"Added technique {args.technique_id}")
    else:
        print(f"Failed to add technique {args.technique_id}")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Autonomous Research System for Security Techniques",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Initialize project
  autonomous-research init
  
  # Run autonomous mode
  autonomous-research run
  
  # Generate content for specific technique
  autonomous-research generate --technique T1003
  
  # Show system status
  autonomous-research status
        """
    )
    
    # Global arguments
    parser.add_argument(
        "--project-dir", 
        default=".",
        help="Project directory (default: current directory)"
    )
    
    parser.add_argument(
        "--model",
        default="llama2-uncensored:7b",
        help="LLM model to use for generation"
    )
    
    # Subcommands
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Init command
    parser_init = subparsers.add_parser("init", help="Initialize project")
    parser_init.set_defaults(func=cmd_init)
    
    # Run command  
    parser_run = subparsers.add_parser("run", help="Run autonomous research")
    parser_run.add_argument(
        "--interval", 
        type=int, 
        default=3600,
        help="Update interval in seconds (default: 3600)"
    )
    parser_run.add_argument(
        "--single-cycle",
        action="store_true", 
        help="Run single cycle instead of continuous"
    )
    parser_run.set_defaults(func=cmd_run)
    
    # Generate command
    parser_gen = subparsers.add_parser("generate", help="Generate content")
    parser_gen.add_argument(
        "--technique",
        dest="technique_id",
        help="Specific technique ID to generate"
    )
    parser_gen.set_defaults(func=cmd_generate)
    
    # Status command
    parser_status = subparsers.add_parser("status", help="Show status")
    parser_status.set_defaults(func=cmd_status)
    
    # Add technique command
    parser_add = subparsers.add_parser("add", help="Add new technique")
    parser_add.add_argument("technique_id", help="Technique ID")
    parser_add.add_argument("name", help="Technique name")
    parser_add.add_argument("--platform", default="Windows", help="Platform")
    parser_add.add_argument("--description", help="Description")
    parser_add.set_defaults(func=cmd_add_technique)
    
    # Parse and execute
    args = parser.parse_args()
    
    if not hasattr(args, 'func'):
        parser.print_help()
        sys.exit(1)
    
    try:
        args.func(args)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
