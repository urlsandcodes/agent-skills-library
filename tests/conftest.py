"""Pytest configuration and shared test fixtures."""

import sys
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.core.loader import load_registry, load_sources


@pytest.fixture
def repo_root():
    return REPO_ROOT


@pytest.fixture
def registry():
    return load_registry()


@pytest.fixture
def sources():
    return load_sources()


@pytest.fixture
def temp_project(tmp_path):
    project_dir = tmp_path / "sample_project"
    project_dir.mkdir()
    return project_dir
