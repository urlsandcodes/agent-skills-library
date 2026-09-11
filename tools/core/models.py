"""Domain models for the Engineering Agent Skills Registry."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any


class SourceType(str, Enum):
    OFFICIAL = "official"
    CURATED_COMMUNITY = "curated_community"
    INTERNAL = "internal"


class SkillType(str, Enum):
    TECHNOLOGY = "technology"
    PRACTICE = "practice"
    INTELLIGENCE = "intelligence"


class SkillStatus(str, Enum):
    OFFICIAL = "official"
    CURATED = "curated"
    INTERNAL = "internal"
    DEPRECATED = "deprecated"


class DependencyKind(str, Enum):
    HARD = "hard"
    RECOMMENDED = "recommended"
    OPTIONAL = "optional"


@dataclass(frozen=True)
class Dependency:
    id: str
    kind: DependencyKind
    version: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Dependency":
        return cls(
            id=data["id"],
            kind=DependencyKind(data.get("kind", "hard")),
            version=data.get("version"),
        )


@dataclass(frozen=True)
class SourceRecord:
    id: str
    provider: str
    repository: str
    source_type: SourceType
    default_branch: str
    pinned_commit: str
    license: str
    verified_at: str
    website: Optional[str] = None
    verification_notes: Optional[str] = None

    @classmethod
    def from_dict(cls, source_id: str, data: Dict[str, Any]) -> "SourceRecord":
        return cls(
            id=source_id,
            provider=data["provider"],
            repository=data["repository"],
            source_type=SourceType(data["source_type"]),
            default_branch=data["default_branch"],
            pinned_commit=data["pinned_commit"],
            license=data["license"],
            verified_at=data["verified_at"],
            website=data.get("website"),
            verification_notes=data.get("verification_notes"),
        )


@dataclass(frozen=True)
class SkillManifest:
    schema_version: str
    id: str
    name: str
    version: str
    type: SkillType
    status: SkillStatus
    category: str
    description: str
    tags: List[str]
    provider: Dict[str, str]
    source: Dict[str, Any]
    capabilities: Dict[str, List[str]]
    dependencies: List[Dependency]
    conflicts: List[str]
    compatibility: Dict[str, Any]
    entrypoints: Dict[str, str]
    update_policy: Dict[str, str]
    file_path: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any], file_path: Optional[str] = None) -> "SkillManifest":
        deps = [Dependency.from_dict(d) for d in data.get("dependencies", [])]
        return cls(
            schema_version=data["schema_version"],
            id=data["id"],
            name=data["name"],
            version=data["version"],
            type=SkillType(data["type"]),
            status=SkillStatus(data["status"]),
            category=data["category"],
            description=data["description"],
            tags=data.get("tags", []),
            provider=data["provider"],
            source=data["source"],
            capabilities=data.get("capabilities", {}),
            dependencies=deps,
            conflicts=data.get("conflicts", []),
            compatibility=data.get("compatibility", {}),
            entrypoints=data["entrypoints"],
            update_policy=data.get("update_policy", {}),
            file_path=file_path,
        )


@dataclass(frozen=True)
class RegistrySkill:
    id: str
    name: str
    version: str
    type: SkillType
    category: str
    status: SkillStatus
    source_id: str
    manifest_path: str
    description: str
    tags: List[str]
    dependencies: List[Dependency] = field(default_factory=list)
    conflicts: List[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RegistrySkill":
        deps = [Dependency.from_dict(d) for d in data.get("dependencies", [])]
        return cls(
            id=data["id"],
            name=data["name"],
            version=data.get("version", "1.0.0"),
            type=SkillType(data["type"]),
            category=data["category"],
            status=SkillStatus(data["status"]),
            source_id=data["source_id"],
            manifest_path=data["manifest_path"],
            description=data.get("description", ""),
            tags=data.get("tags", []),
            dependencies=deps,
            conflicts=data.get("conflicts", []),
        )


@dataclass
class InstalledSkillRecord:
    version: str
    source_type: str
    repository: str
    commit: str
    integrity: str
    install_reason: str
    dependencies: List[str]
    installed_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        data = {
            "version": self.version,
            "source_type": self.source_type,
            "repository": self.repository,
            "commit": self.commit,
            "integrity": self.integrity,
            "install_reason": self.install_reason,
            "dependencies": self.dependencies,
        }
        if self.installed_at:
            data["installed_at"] = self.installed_at
        return data


@dataclass
class SkillsLockfile:
    lockfile_version: int
    generated_at: str
    target_directory: str
    skills: Dict[str, InstalledSkillRecord]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "lockfile_version": self.lockfile_version,
            "generated_at": self.generated_at,
            "target_directory": self.target_directory,
            "skills": {k: v.to_dict() for k, v in sorted(self.skills.items())},
        }
