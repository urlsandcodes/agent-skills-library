"""Checks installed project skills against the master registry and applies updates safely."""

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional
from tools.core.loader import load_registry, load_manifest
from tools.core.models import RegistrySkill
from tools.installer.lockfile import LockfileManager
from tools.installer.stage import AtomicInstaller
from tools.resolver.graph import ResolvedSkill


@dataclass
class SkillUpdateStatus:
    skill_id: str
    installed_version: str
    installed_commit: str
    registry_version: str
    registry_commit: str
    status: str  # 'up-to-date', 'update-available', 'untracked'

    def to_dict(self) -> Dict:
        return {
            "skill_id": self.skill_id,
            "installed_version": self.installed_version,
            "installed_commit": self.installed_commit[:8] if self.installed_commit != "local" else "local",
            "registry_version": self.registry_version,
            "registry_commit": self.registry_commit[:8] if self.registry_commit != "local" else "local",
            "status": self.status,
        }


class SkillUpdater:
    def __init__(self, repo_root: Path, project_root: Path):
        self.repo_root = repo_root
        self.project_root = project_root
        self.lockfile_mgr = LockfileManager(project_root)

    def check_updates(self, registry: Dict[str, RegistrySkill]) -> List[SkillUpdateStatus]:
        lockfile = self.lockfile_mgr.load()
        statuses: List[SkillUpdateStatus] = []

        for skill_id, record in lockfile.skills.items():
            if skill_id not in registry:
                statuses.append(
                    SkillUpdateStatus(
                        skill_id=skill_id,
                        installed_version=record.version,
                        installed_commit=record.commit,
                        registry_version="unknown",
                        registry_commit="unknown",
                        status="untracked",
                    )
                )
                continue

            reg_skill = registry[skill_id]
            m_path = self.repo_root / reg_skill.manifest_path
            manifest = load_manifest(m_path)
            reg_commit = manifest.source.get("commit", "")
            reg_version = manifest.version

            if record.commit == reg_commit and record.version == reg_version:
                st = "up-to-date"
            else:
                st = "update-available"

            statuses.append(
                SkillUpdateStatus(
                    skill_id=skill_id,
                    installed_version=record.version,
                    installed_commit=record.commit,
                    registry_version=reg_version,
                    registry_commit=reg_commit,
                    status=st,
                )
            )

        return statuses

    def apply_updates(self, registry: Dict[str, RegistrySkill]) -> List[SkillUpdateStatus]:
        updates = self.check_updates(registry)
        to_update = [u for u in updates if u.status == "update-available"]

        if not to_update:
            return updates

        installer = AtomicInstaller(self.repo_root, self.project_root)
        resolved = [
            ResolvedSkill(id=u.skill_id, install_reason="update", dependencies=[])
            for u in to_update
        ]
        installer.install_resolved(resolved, registry, force=True)
        return self.check_updates(registry)
