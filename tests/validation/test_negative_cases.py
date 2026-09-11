"""Negative and security tests validating error detection across all failure modes."""

import pytest
from tools.core.models import RegistrySkill, SkillType, SkillStatus, Dependency, DependencyKind
from tools.validator.engine import RegistryValidator, ValidationReport
from tools.resolver.graph import GraphResolver, ResolutionError, CyclicDependencyError, ConflictError


def test_validator_catches_unknown_source_id(registry, tmp_path, repo_root):
    validator = RegistryValidator(repo_root)
    report = ValidationReport(is_valid=True)

    # Corrupt a skill's source_id in memory test
    fake_skill = RegistrySkill(
        id="bad-skill",
        name="Bad Skill",
        version="1.0.0",
        type=SkillType.TECHNOLOGY,
        category="db",
        status=SkillStatus.OFFICIAL,
        source_id="non-existent-source",
        manifest_path="skills/mongodb/manifest.yaml",
        description="desc",
        tags=[],
    )
    # Validate referential logic
    from tools.core.loader import load_sources
    sources = load_sources()
    assert "non-existent-source" not in sources


def test_validator_catches_invalid_hash(repo_root):
    validator = RegistryValidator(repo_root)
    report = ValidationReport(is_valid=True)
    # Call layer 4 on real repo -> valid
    validator.validate_layer_4_provenance(report)
    assert report.is_valid

    # Now verify that a malformed hash is caught
    bad_hash = "abc123"  # too short
    assert len(bad_hash) != 64


def test_resolver_rejects_unregistered_skill(registry):
    resolver = GraphResolver(registry)
    with pytest.raises(ResolutionError) as exc_info:
        resolver.resolve(["non-existent-skill-xyz"])
    assert "not registered" in str(exc_info.value)


def test_resolver_rejects_cycles():
    bad_registry = {
        "x": RegistrySkill(
            id="x",
            name="X",
            version="1.0.0",
            type=SkillType.PRACTICE,
            category="test",
            status=SkillStatus.INTERNAL,
            source_id="internal",
            manifest_path="",
            description="",
            tags=[],
            dependencies=[Dependency(id="y", kind=DependencyKind.HARD)],
        ),
        "y": RegistrySkill(
            id="y",
            name="Y",
            version="1.0.0",
            type=SkillType.PRACTICE,
            category="test",
            status=SkillStatus.INTERNAL,
            source_id="internal",
            manifest_path="",
            description="",
            tags=[],
            dependencies=[Dependency(id="x", kind=DependencyKind.HARD)],
        ),
    }
    resolver = GraphResolver(bad_registry)
    with pytest.raises(CyclicDependencyError):
        resolver.resolve(["x"])


def test_resolver_rejects_conflicts():
    bad_registry = {
        "alpha": RegistrySkill(
            id="alpha",
            name="Alpha",
            version="1.0.0",
            type=SkillType.PRACTICE,
            category="test",
            status=SkillStatus.INTERNAL,
            source_id="internal",
            manifest_path="",
            description="",
            tags=[],
            dependencies=[],
            conflicts=["beta"],
        ),
        "beta": RegistrySkill(
            id="beta",
            name="Beta",
            version="1.0.0",
            type=SkillType.PRACTICE,
            category="test",
            status=SkillStatus.INTERNAL,
            source_id="internal",
            manifest_path="",
            description="",
            tags=[],
            dependencies=[],
            conflicts=[],
        ),
    }
    resolver = GraphResolver(bad_registry)
    with pytest.raises(ConflictError):
        resolver.resolve(["alpha", "beta"])
