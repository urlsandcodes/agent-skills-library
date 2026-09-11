"""Configuration constants and standard directory paths for the registry."""

from pathlib import Path

# Find repo root dynamically
REPO_ROOT = Path(__file__).resolve().parent.parent.parent

REGISTRY_PATH = REPO_ROOT / "registry.yaml"
SOURCES_PATH = REPO_ROOT / "sources.yaml"
SCHEMAS_DIR = REPO_ROOT / "schemas"
SKILLS_DIR = REPO_ROOT / "skills"
ENGINEERING_DIR = REPO_ROOT / "engineering"

REGISTRY_SCHEMA_PATH = SCHEMAS_DIR / "registry.schema.json"
SOURCES_SCHEMA_PATH = SCHEMAS_DIR / "sources.schema.json"
MANIFEST_SCHEMA_PATH = SCHEMAS_DIR / "manifest.schema.json"
LOCKFILE_SCHEMA_PATH = SCHEMAS_DIR / "lockfile.schema.json"

# Project-level standard directory paths
DEFAULT_PROJECT_SKILLS_SUBDIR = ".agents/skills"
DEFAULT_LOCKFILE_NAME = ".agents/skills.lock.yaml"
DEFAULT_ARCHITECTURE_PATH = ".agents/architecture.md"
