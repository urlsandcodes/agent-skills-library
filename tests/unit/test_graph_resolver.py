"""Unit tests for dependency graph resolution and cycle detection."""

import pytest
from tools.core.models import Dependency, DependencyKind, RegistrySkill, SkillStatus, SkillType
from tools.resolver.graph import ConflictError, CyclicDependencyError, GraphResolver, ResolutionError


def test_resolve_with_dependencies(registry):
    resolver = GraphResolver(registry)
    # nextjs has hard dependency on nodejs and recommended on testing
    resolved = resolver.resolve(["nextjs"], include_recommended=True)
    resolved_ids = [r.id for r in resolved]
    assert "nextjs" in resolved_ids
    assert "nodejs" in resolved_ids
    assert "testing" in resolved_ids


def test_resolve_without_recommended(registry):
    resolver = GraphResolver(registry)
    # nextjs has hard dependency on nodejs, recommended on testing
    resolved = resolver.resolve(["nextjs"], include_recommended=False)
    resolved_ids = [r.id for r in resolved]
    assert "nextjs" in resolved_ids
    assert "nodejs" in resolved_ids
    assert "testing" not in resolved_ids


def test_cycle_detection():
    # Synthetic cyclic graph: A -> B -> A
    cyclic_skills = {
        "skill-a": RegistrySkill(
            id="skill-a",
            name="Skill A",
            version="1.0.0",
            type=SkillType.TECHNOLOGY,
            category="test",
            status=SkillStatus.INTERNAL,
            source_id="internal",
            manifest_path="",
            description="",
            tags=[],
            dependencies=[Dependency(id="skill-b", kind=DependencyKind.HARD)],
        ),
        "skill-b": RegistrySkill(
            id="skill-b",
            name="Skill B",
            version="1.0.0",
            type=SkillType.TECHNOLOGY,
            category="test",
            status=SkillStatus.INTERNAL,
            source_id="internal",
            manifest_path="",
            description="",
            tags=[],
            dependencies=[Dependency(id="skill-a", kind=DependencyKind.HARD)],
        ),
    }
    resolver = GraphResolver(cyclic_skills)
    with pytest.raises(CyclicDependencyError) as exc_info:
        resolver.resolve(["skill-a"])
    assert "Cyclic dependency detected" in str(exc_info.value)


def test_conflict_detection():
    # Synthetic conflict graph: A conflicts with B
    conflicting_skills = {
        "skill-a": RegistrySkill(
            id="skill-a",
            name="Skill A",
            version="1.0.0",
            type=SkillType.TECHNOLOGY,
            category="test",
            status=SkillStatus.INTERNAL,
            source_id="internal",
            manifest_path="",
            description="",
            tags=[],
            dependencies=[],
            conflicts=["skill-b"],
        ),
        "skill-b": RegistrySkill(
            id="skill-b",
            name="Skill B",
            version="1.0.0",
            type=SkillType.TECHNOLOGY,
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
    resolver = GraphResolver(conflicting_skills)
    with pytest.raises(ConflictError) as exc_info:
        resolver.resolve(["skill-a", "skill-b"])
    assert "Conflict detected" in str(exc_info.value)
