"""
Integration module for Autonomous Research System.

Provides integration capabilities for migrating to new system architectures
and output formats.
"""

from .json_output_migration import (
    OutputSystemMigration,
    AutonomousSystemIntegration,
    integrate_json_output_system
)

__all__ = [
    "OutputSystemMigration",
    "AutonomousSystemIntegration", 
    "integrate_json_output_system"
]
