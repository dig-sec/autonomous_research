"""
Entry point for Autonomous Research System
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from src.autonomous_research.core.autonomous_system import AutonomousResearchSystem

def main():
    ars = AutonomousResearchSystem()
    ars.run_autonomous()

if __name__ == "__main__":
    main()
