#!/usr/bin/env python3
"""
Validate project structure and check for misplaced or missing files.
"""

import os
import sys
from pathlib import Path

EXPECTED_FOLDERS = [
    "demos",
    "integration",
    "utils",
    "knowledge"
]

def validate_structure(base_path):
    print(f"Validating project structure in: {base_path}")
    missing = []
    for folder in EXPECTED_FOLDERS:
        folder_path = Path(base_path) / folder
        if not folder_path.exists():
            missing.append(folder)
    if missing:
        print(f"❌ Missing folders: {', '.join(missing)}")
    else:
        print("✅ All expected folders are present.")

    # Check for misplaced files in root
    root_files = [f for f in Path(base_path).iterdir() if f.is_file() and f.suffix == '.py']
    if root_files:
        print("⚠️  Misplaced Python files in root:")
        for f in root_files:
            print(f"  - {f.name}")
    else:
        print("✅ No misplaced Python files in root.")

if __name__ == "__main__":
    base = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(__file__)
    validate_structure(base)
