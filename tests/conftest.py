"""Shared fixtures for article companion tests."""

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
EXAMPLES_DIR = REPO_ROOT / "examples"


@pytest.fixture
def examples_dir():
    return EXAMPLES_DIR


@pytest.fixture
def yaml_files():
    """Return all YAML files in the examples directory."""
    return sorted(EXAMPLES_DIR.rglob("*.yaml"))


@pytest.fixture
def python_files():
    """Return all Python files in the examples directory."""
    return sorted(EXAMPLES_DIR.rglob("*.py"))


@pytest.fixture
def bash_files():
    """Return all bash scripts in the examples directory."""
    return sorted(EXAMPLES_DIR.rglob("*.sh"))
