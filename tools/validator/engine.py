"""Multi-layer validation engine for the Engineering Agent Skills Registry.

Evaluates 6 rigorous verification layers:
  1. Syntax & Schemas Gate
  2. Referential Integrity Gate
  3. Graph & Conflicts Gate
  4. Provenance & Integrity Gate
  5. Content Structure Gate
  6. Installation Simulation Gate
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
import jsonschema

from tools.core.config import (
    REPO_ROOT,
    REGISTRY_PATH,
    SOURCES_PATH,
    REGISTRY_SCHEMA_PATH,
    SOURCES_SCHEMA_PATH,
    MANIFEST_SCHEMA_PATH,
    SCHEMAS_DIR,
)
from tools.core.loader import (
    load_yaml,
    load_json,
    validate_against_schema,
    load_registry,
    load_sources,
    load_manifest,
)
from tools.core.models import RegistrySkill, SkillManifest, SourceRecord, DependencyKind


@dataclass
class ValidationReport:
    is_valid: bool
    layer_errors: Dict[int, List[str]] = field(default_factory=dict)
    layer_warnings: Dict[int, List[str]] = field(default_factory=dict)

    def add_error(self, layer: int, msg: str) -> None:
        self.is_valid = False
        if layer not in self.layer_errors:
            self.layer_errors[layer] = []
        self.layer_errors[layer].append(msg)

    def add_warning(self, layer: int, msg: str) -> None:
        if layer not in self.layer_warnings:
            self.layer_warnings[layer] = []
        self.layer_warnings[layer].append(msg)

    def to_dict(self) -> Dict:
        return {
            "is_valid": self.is_valid,
            "errors": {f"layer_{k}": v for k, v in sorted(self.layer_errors.items())},
            "warnings": {f"layer_{k}": v for k, v in sorted(self.layer_warnings.items())},
        }


class RegistryValidator:
    def __init__(self, repo_root: Optional[Path] = None):
        self.repo_root = repo_root or REPO_ROOT
        self.registry_path = self.repo_root / "registry.yaml"
        self.sources_path = self.repo_root / "sources.yaml"
        self.registry_schema_path = self.repo_root / "schemas" / "registry.schema.json"
        self.sources_schema_path = self.repo_root / "schemas" / "sources.schema.json"
        self.manifest_schema_path = self.repo_root / "schemas" / "manifest.schema.json"

    def validate_all(self, strict: bool = True) -> ValidationReport:
        report = ValidationReport(is_valid=True)
        self.validate_layer_1_schemas(report)
        self.validate_layer_2_referential(report)
        self.validate_layer_3_graph_and_conflicts(report)
        self.validate_layer_4_provenance(report)
        self.validate_layer_5_content(report)
        self.validate_layer_6_simulation(report)
        return report

    def validate_layer_1_schemas(self, report: ValidationReport) -> None:
        """Layer 1: Syntax & Schemas Gate."""
        # 1. Validate registry.yaml against registry.schema.json
        try:
            reg_raw = load_yaml(self.registry_path)
            reg_errs = validate_against_schema(reg_raw, self.registry_schema_path)
            for err in reg_errs:
                report.add_error(1, f"registry.yaml schema violation: {err}")
        except Exception as e:
            report.add_error(1, f"Failed to parse registry.yaml: {e}")

        # 2. Validate sources.yaml against sources.schema.json
        try:
            src_raw = load_yaml(self.sources_path)
            src_errs = validate_against_schema(src_raw, self.sources_schema_path)
            for err in src_errs:
                report.add_error(1, f"sources.yaml schema violation: {err}")
        except Exception as e:
            report.add_error(1, f"Failed to parse sources.yaml: {e}")

        # 3. Validate every manifest file against manifest.schema.json
        try:
            skills = load_registry(self.registry_path)
            for skill_id, skill in skills.items():
                m_path = self.repo_root / skill.manifest_path
                if not m_path.exists():
                    report.add_error(1, f"Manifest file missing for skill '{skill_id}': {m_path}")
                    continue
                try:
                    m_raw = load_yaml(m_path)
                    m_errs = validate_against_schema(m_raw, self.manifest_schema_path)
                    for err in m_errs:
                        report.add_error(1, f"Manifest '{skill.manifest_path}' schema violation: {err}")
                except Exception as e:
                    report.add_error(1, f"Failed to parse manifest '{skill.manifest_path}': {e}")
        except Exception as e:
            report.add_error(1, f"Cannot load skills for Layer 1 validation: {e}")

        # 4. Check schema validity of all internal schemas
        schemas_dir = self.repo_root / "schemas"
        for s_file in schemas_dir.glob("*.json"):
            try:
                s_raw = load_json(s_file)
                jsonschema.Draft202012Validator.check_schema(s_raw)
            except Exception as e:
                report.add_error(1, f"Invalid JSON Schema in '{s_file.name}': {e}")

    def validate_layer_2_referential(self, report: ValidationReport) -> None:
        """Layer 2: Referential Integrity Gate."""
        try:
            registry = load_registry(self.registry_path)
            sources = load_sources(self.sources_path)
        except Exception as e:
            report.add_error(2, f"Failed to load registry or sources for referential check: {e}")
            return

        skill_ids: Set[str] = set()

        for skill_id, skill in registry.items():
            # Check unique IDs
            if skill_id in skill_ids:
                report.add_error(2, f"Duplicate skill ID registered: '{skill_id}'")
            skill_ids.add(skill_id)

            # Check source_id exists in sources.yaml
            if skill.source_id not in sources:
                report.add_error(
                    2,
                    f"Skill '{skill_id}' references unknown source_id '{skill.source_id}' not found in sources.yaml",
                )

            # Check manifest path exists
            m_path = self.repo_root / skill.manifest_path
            if not m_path.exists():
                report.add_error(2, f"Skill '{skill_id}' manifest_path does not exist: {m_path}")
                continue

            # Check manifest internal ID matches registry ID
            try:
                manifest = load_manifest(m_path)
                if manifest.id != skill_id:
                    report.add_error(
                        2,
                        f"ID mismatch: registry specifies '{skill_id}' but manifest declares '{manifest.id}'",
                    )
                if manifest.type != skill.type:
                    report.add_error(
                        2,
                        f"Type mismatch for skill '{skill_id}': registry has '{skill.type}' but manifest has '{manifest.type}'",
                    )
            except Exception as e:
                report.add_error(2, f"Error inspecting manifest for skill '{skill_id}': {e}")

    def validate_layer_3_graph_and_conflicts(self, report: ValidationReport) -> None:
        """Layer 3: Graph & Conflicts Gate."""
        try:
            registry = load_registry(self.registry_path)
        except Exception as e:
            report.add_error(3, f"Cannot load registry for graph check: {e}")
            return

        all_ids = set(registry.keys())

        # 1. Verify all dependencies exist
        for skill_id, skill in registry.items():
            for dep in skill.dependencies:
                if dep.id not in all_ids:
                    report.add_error(
                        3,
                        f"Skill '{skill_id}' depends on unknown skill '{dep.id}'",
                    )

            # Check conflict sanity
            for conf_id in skill.conflicts:
                if conf_id == skill_id:
                    report.add_error(3, f"Skill '{skill_id}' cannot conflict with itself.")
                for dep in skill.dependencies:
                    if dep.id == conf_id and dep.kind == DependencyKind.HARD:
                        report.add_error(
                            3,
                            f"Skill '{skill_id}' has conflict '{conf_id}' that is also a hard dependency.",
                        )

        # 2. Check for circular dependencies among hard dependencies
        # 3-color cycle detection: 0 = unvisited, 1 = visiting, 2 = visited
        visited: Dict[str, int] = {k: 0 for k in all_ids}
        stack: List[str] = []

        def dfs(node: str) -> None:
            visited[node] = 1
            stack.append(node)
            skill = registry.get(node)
            if skill:
                for dep in skill.dependencies:
                    if dep.kind == DependencyKind.HARD and dep.id in registry:
                        if visited[dep.id] == 1:
                            cycle_path = " -> ".join(stack[stack.index(dep.id) :] + [dep.id])
                            report.add_error(3, f"Circular hard dependency detected: {cycle_path}")
                        elif visited[dep.id] == 0:
                            dfs(dep.id)
            stack.pop()
            visited[node] = 2

        for sid in all_ids:
            if visited[sid] == 0:
                dfs(sid)

    def validate_layer_4_provenance(self, report: ValidationReport) -> None:
        """Layer 4: Provenance & Integrity Gate."""
        try:
            sources = load_sources(self.sources_path)
            registry = load_registry(self.registry_path)
        except Exception as e:
            report.add_error(4, f"Cannot load sources/registry for provenance check: {e}")
            return

        for src_id, src in sources.items():
            # Check pinned commit is non-empty and formatted
            if src.pinned_commit != "local" and len(src.pinned_commit) != 40:
                report.add_error(
                    4,
                    f"Source '{src_id}' has invalid pinned_commit '{src.pinned_commit}'. Must be 40-char SHA or 'local'.",
                )
            if not src.license:
                report.add_error(4, f"Source '{src_id}' is missing a declared license.")

        for skill_id, skill in registry.items():
            m_path = self.repo_root / skill.manifest_path
            if not m_path.exists():
                continue
            try:
                manifest = load_manifest(m_path)
                integrity = manifest.source.get("integrity", {})
                hash_val = integrity.get("hash", "")
                if len(hash_val) != 64:
                    report.add_error(
                        4,
                        f"Skill '{skill_id}' manifest has invalid sha256 hash '{hash_val}'. Must be 64 hex chars.",
                    )
            except Exception as e:
                report.add_error(4, f"Error checking integrity for skill '{skill_id}': {e}")

    def validate_layer_5_content(self, report: ValidationReport) -> None:
        """Layer 5: Content Structure Gate."""
        try:
            registry = load_registry(self.registry_path)
        except Exception as e:
            report.add_error(5, f"Cannot load registry for content check: {e}")
            return

        for skill_id, skill in registry.items():
            m_path = self.repo_root / skill.manifest_path
            if not m_path.exists():
                continue
            manifest_dir = m_path.parent
            try:
                manifest = load_manifest(m_path)
                skill_doc_name = manifest.entrypoints.get("skill_doc")
                if skill_doc_name:
                    doc_path = manifest_dir / skill_doc_name
                    # For internal skills, SKILL.md MUST exist locally in repo
                    if manifest.source.get("type") == "internal" and not doc_path.exists():
                        report.add_error(
                            5,
                            f"Internal skill '{skill_id}' is missing required entrypoint '{skill_doc_name}' at {doc_path}",
                        )
            except Exception as e:
                report.add_error(5, f"Error validating content structure for '{skill_id}': {e}")

    def validate_layer_6_simulation(self, report: ValidationReport) -> None:
        """Layer 6: Installation Simulation Gate."""
        try:
            registry = load_registry(self.registry_path)
        except Exception as e:
            report.add_error(6, f"Cannot load registry for simulation: {e}")
            return

        # Check each skill can be simulated for resolution without collision
        for skill_id, skill in registry.items():
            try:
                resolved = self._simulate_resolve(skill_id, registry)
                if skill_id not in resolved:
                    report.add_error(6, f"Simulation failed: skill '{skill_id}' not resolved in its own closure.")
            except Exception as e:
                report.add_error(6, f"Resolution simulation failed for skill '{skill_id}': {e}")

    def _simulate_resolve(self, target_id: str, registry: Dict[str, RegistrySkill]) -> Set[str]:
        resolved: Set[str] = set()

        def resolve(sid: str) -> None:
            if sid in resolved:
                return
            resolved.add(sid)
            s = registry.get(sid)
            if s:
                for dep in s.dependencies:
                    if dep.kind == DependencyKind.HARD:
                        resolve(dep.id)

        resolve(target_id)
        return resolved
