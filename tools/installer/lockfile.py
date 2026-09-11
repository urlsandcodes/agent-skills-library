"""Lockfile management for project-local skill dependencies (.agents/skills.lock.yaml)."""

from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional
from tools.core.config import DEFAULT_LOCKFILE_NAME
from tools.core.loader import load_yaml, dump_yaml, validate_against_schema
from tools.core.models import InstalledSkillRecord, SkillsLockfile


class LockfileManager:
    def __init__(self, project_root: Path, schema_path: Optional[Path] = None):
        self.project_root = project_root
        self.lockfile_path = project_root / DEFAULT_LOCKFILE_NAME
        self.schema_path = schema_path

    def exists(self) -> bool:
        return self.lockfile_path.exists()

    def load(self) -> SkillsLockfile:
        if not self.exists():
            return SkillsLockfile(
                lockfile_version=1,
                generated_at=datetime.now(timezone.utc).isoformat(),
                target_directory=".agents/skills",
                skills={},
            )
        data = load_yaml(self.lockfile_path)
        skills = {}
        for sid, item in data.get("skills", {}).items():
            skills[sid] = InstalledSkillRecord(
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
            target_directory=data.get("target_directory", ".agents/skills"),
            skills=skills,
        )

    def save(self, lockfile: SkillsLockfile) -> None:
        data = lockfile.to_dict()
        if self.schema_path and self.schema_path.exists():
            errors = validate_against_schema(data, self.schema_path)
            if errors:
                raise ValueError(f"Generated lockfile violates schema: {errors}")
        dump_yaml(data, self.lockfile_path)

    def record_skill(
        self,
        skill_id: str,
        version: str,
        source_type: str,
        repository: str,
        commit: str,
        integrity: str,
        install_reason: str,
        dependencies: List[str],
    ) -> None:
        lockfile = self.load()
        lockfile.skills[skill_id] = InstalledSkillRecord(
            version=version,
            source_type=source_type,
            repository=repository,
            commit=commit,
            integrity=integrity,
            install_reason=install_reason,
            dependencies=dependencies,
            installed_at=datetime.now(timezone.utc).isoformat(),
        )
        lockfile.generated_at = datetime.now(timezone.utc).isoformat()
        self.save(lockfile)
