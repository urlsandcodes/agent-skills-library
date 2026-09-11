"""Safe YAML/JSON loading, serialization, and schema validation helpers."""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
import yaml
import jsonschema

from tools.core.config import (
    REGISTRY_PATH,
    SOURCES_PATH,
    REGISTRY_SCHEMA_PATH,
    SOURCES_SCHEMA_PATH,
    MANIFEST_SCHEMA_PATH,
    LOCKFILE_SCHEMA_PATH,
)
from tools.core.models import RegistrySkill, SkillManifest, SourceRecord, SkillsLockfile, InstalledSkillRecord


def load_yaml(file_path: Path) -> Any:
    """Safely loads a YAML file using PyYAML safe_load."""
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    with open(file_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def dump_yaml(data: Any, file_path: Path) -> None:
    """Safely dumps data to a YAML file preserving formatting."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, sort_keys=False, default_flow_style=False)


def load_json(file_path: Path) -> Any:
    """Loads a JSON file."""
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_against_schema(data: Any, schema_path: Path) -> List[str]:
    """Validates data against a JSON Schema Draft 2020-12 and returns a list of error strings."""
    schema = load_json(schema_path)
    validator = jsonschema.Draft202012Validator(schema)
    errors = []
    for err in validator.iter_errors(data):
        loc = " -> ".join([str(p) for p in err.absolute_path]) if err.absolute_path else "root"
        errors.append(f"[{loc}] {err.message}")
    return errors


def load_registry(path: Optional[Path] = None) -> Dict[str, RegistrySkill]:
    """Loads and parses the master registry.yaml into a dict of id -> RegistrySkill."""
    reg_path = path or REGISTRY_PATH
    data = load_yaml(reg_path)
    skills = {}
    for item in data.get("skills", []):
        skill = RegistrySkill.from_dict(item)
        skills[skill.id] = skill
    return skills


def load_sources(path: Optional[Path] = None) -> Dict[str, SourceRecord]:
    """Loads and parses sources.yaml into a dict of id -> SourceRecord."""
    src_path = path or SOURCES_PATH
    data = load_yaml(src_path)
    sources = {}
    for src_id, item in data.get("sources", {}).items():
        sources[src_id] = SourceRecord.from_dict(src_id, item)
    return sources


def load_manifest(file_path: Path) -> SkillManifest:
    """Loads and parses a single skill manifest.yaml into a SkillManifest model."""
    data = load_yaml(file_path)
    return SkillManifest.from_dict(data, file_path=str(file_path))


def load_lockfile(file_path: Path) -> SkillsLockfile:
    """Loads an existing .agents/skills.lock.yaml."""
    data = load_yaml(file_path)
    skills = {}
    for skill_id, item in data.get("skills", {}).items():
        skills[skill_id] = InstalledSkillRecord(
            version=item["version"],
            source_type=item["source_type"],
            repository=item["repository"],
            commit=item["commit"],
            integrity=item["integrity"],
            install_reason=item["install_reason"],
            dependencies=item.get("dependencies", []),
            installed_at=item.get("installed_at"),
        )
    return SkillsLockfile(
        lockfile_version=data["lockfile_version"],
        generated_at=data["generated_at"],
        target_directory=data["target_directory"],
        skills=skills,
    )
