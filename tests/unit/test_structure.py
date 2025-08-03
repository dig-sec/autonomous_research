import os
import pytest
from pathlib import Path

def test_src_structure():
    root = Path(__file__).parent.parent.parent / 'src' / 'autonomous_research'
    expected_dirs = [
        'core', 'config', 'generation', 'rag', 'research', 'utils', 'models'
    ]
    for d in expected_dirs:
        assert (root / d).exists(), f"Missing directory: {d}"
        assert (root / d).is_dir(), f"{d} is not a directory"
    assert (root / '__init__.py').exists(), "Missing __init__.py in autonomous_research"

def test_no_legacy_dirs():
    project_root = Path(__file__).parent.parent.parent
    legacy_dirs = ['autonomous_research', 'config']
    for d in legacy_dirs:
        assert not (project_root / d).exists(), f"Legacy directory still exists: {d}"

def test_config_module():
    config_dir = Path(__file__).parent.parent.parent / 'src' / 'autonomous_research' / 'config'
    assert (config_dir / 'secure_config.py').exists(), "Missing secure_config.py in config module"
