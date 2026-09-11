"""Unit tests for YAML/JSON loader and serialization."""

from tools.core.loader import load_registry, load_sources, load_manifest
from tools.core.config import REPO_ROOT


def test_load_registry_returns_all_skills():
    registry = load_registry()
    assert len(registry) >= 8
    assert "mongodb" in registry
    assert "flutter" in registry
    assert "architecture.system-validator" in registry


def test_load_sources_contains_verified_providers():
    sources = load_sources()
    assert "mongodb" in sources
    assert sources["mongodb"].source_type.value == "official"
    assert sources["mongodb"].pinned_commit != "main"


def test_load_manifest_structure():
    manifest_path = REPO_ROOT / "skills/mongodb/manifest.yaml"
    manifest = load_manifest(manifest_path)
    assert manifest.id == "mongodb"
    assert manifest.status.value == "official"
    assert "database" in manifest.tags
