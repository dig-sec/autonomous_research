#!/usr/bin/env python3
"""
Migrate project structure utility

Moves misplaced files to their correct locations based on project conventions.
"""

import os
import shutil
from pathlib import Path

MOVE_MAP = {
    "custom_techniques_demo.py": "demos/custom_techniques_demo.py",
    "clustering_analysis.py": "demos/clustering_analysis.py",
    "demo_non_mitre_handling.py": "demos/demo_non_mitre_handling.py",
    "integration_status.py": "integration/integration_status.py",
    "integration_test.py": "integration/integration_test.py",
    "validate_structure.py": "utils/validate_structure.py",
    "migrate_structure.py": "utils/migrate_structure.py",
    "restructure_project.py": "utils/restructure_project.py"
}

def migrate_files(base_path):
    for src, dest in MOVE_MAP.items():
        src_path = Path(base_path) / src
        dest_path = Path(base_path) / "src" / "autonomous_research" / dest
        if src_path.exists():
            print(f"Moving {src_path} -> {dest_path}")
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src_path), str(dest_path))
        else:
            print(f"File not found: {src_path}")

if __name__ == "__main__":
    base = os.path.dirname(__file__)
    migrate_files(base)
