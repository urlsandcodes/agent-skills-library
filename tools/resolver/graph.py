"""Dependency graph resolution and conflict detection engine."""

from dataclasses import dataclass
from typing import Dict, List, Optional, Set
from tools.core.models import RegistrySkill, DependencyKind


class ResolutionError(Exception):
    pass


class CyclicDependencyError(ResolutionError):
    pass


class ConflictError(ResolutionError):
    pass


@dataclass
class ResolvedSkill:
    id: str
    install_reason: str  # 'direct', 'dependency', 'recommended'
    dependencies: List[str]


class GraphResolver:
    def __init__(self, registry: Dict[str, RegistrySkill]):
        self.registry = registry

    def resolve(
        self,
        target_ids: List[str],
        include_recommended: bool = True,
    ) -> List[ResolvedSkill]:
        """Resolves target skill IDs into an ordered, conflict-free installation list."""
        for tid in target_ids:
            if tid not in self.registry:
                raise ResolutionError(f"Requested skill '{tid}' is not registered in the master catalog.")

        resolved: Dict[str, ResolvedSkill] = {}
        visited: Dict[str, int] = {}  # 0=unvisited, 1=visiting, 2=visited
        stack: List[str] = []

        def dfs(skill_id: str, reason: str) -> None:
            if visited.get(skill_id) == 1:
                cycle = " -> ".join(stack[stack.index(skill_id) :] + [skill_id])
                raise CyclicDependencyError(f"Cyclic dependency detected: {cycle}")
            if visited.get(skill_id) == 2:
                return

            visited[skill_id] = 1
            stack.append(skill_id)
            skill = self.registry[skill_id]

            direct_deps: List[str] = []
            for dep in skill.dependencies:
                if dep.id not in self.registry:
                    raise ResolutionError(f"Skill '{skill_id}' references unknown dependency '{dep.id}'.")

                if dep.kind == DependencyKind.HARD:
                    direct_deps.append(dep.id)
                    dfs(dep.id, reason="dependency")
                elif dep.kind == DependencyKind.RECOMMENDED and include_recommended:
                    direct_deps.append(dep.id)
                    dfs(dep.id, reason="recommended")

            stack.pop()
            visited[skill_id] = 2

            if skill_id not in resolved:
                resolved[skill_id] = ResolvedSkill(
                    id=skill_id,
                    install_reason=reason,
                    dependencies=direct_deps,
                )

        # Process all directly requested skills
        for tid in target_ids:
            dfs(tid, reason="direct")

        # Conflict checking
        resolved_ids = set(resolved.keys())
        for sid in resolved_ids:
            skill = self.registry[sid]
            for conf in skill.conflicts:
                if conf in resolved_ids:
                    raise ConflictError(
                        f"Conflict detected: skill '{sid}' conflicts with '{conf}' in the resolved set."
                    )

        return list(resolved.values())
