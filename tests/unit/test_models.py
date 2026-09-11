"""Unit tests for domain models."""

from tools.core.models import (
    Dependency,
    DependencyKind,
    InstalledSkillRecord,
    RegistrySkill,
    SkillStatus,
    SkillType,
    SkillsLockfile,
    SourceRecord,
    SourceType,
)


def test_dependency_parsing():
    data = {"id": "testing", "kind": "hard", "version": "^1.0.0"}
    dep = Dependency.from_dict(data)
    assert dep.id == "testing"
    assert dep.kind == DependencyKind.HARD
    assert dep.version == "^1.0.0"


def test_source_record_parsing():
    data = {
        "provider": "MongoDB Inc.",
        "repository": "mongodb/agent-skills",
        "source_type": "official",
        "default_branch": "main",
        "pinned_commit": "4f7a1b8c9d0e2f3a4b5c6d7e8f9a0b1c2d3e4f5a",
        "license": "Apache-2.0",
        "verified_at": "2026-09-11T10:00:00Z",
    }
    src = SourceRecord.from_dict("mongodb", data)
    assert src.id == "mongodb"
    assert src.provider == "MongoDB Inc."
    assert src.source_type == SourceType.OFFICIAL
    assert src.pinned_commit == "4f7a1b8c9d0e2f3a4b5c6d7e8f9a0b1c2d3e4f5a"


def test_lockfile_serialization():
    skills = {
        "mongodb": InstalledSkillRecord(
            version="1.2.0",
            source_type="official",
            repository="mongodb/agent-skills",
            commit="4f7a1b8c9d0e2f3a4b5c6d7e8f9a0b1c2d3e4f5a",
            integrity="sha256:abc",
            install_reason="direct",
            dependencies=["testing"],
        )
    }
    lockfile = SkillsLockfile(
        lockfile_version=1,
        generated_at="2026-09-11T10:00:00Z",
        target_directory=".agents/skills",
        skills=skills,
    )
    d = lockfile.to_dict()
    assert d["lockfile_version"] == 1
    assert "mongodb" in d["skills"]
    assert d["skills"]["mongodb"]["version"] == "1.2.0"
