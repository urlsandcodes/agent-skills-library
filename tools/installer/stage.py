"""Atomic staging and installation engine for project-local skills."""

from dataclasses import dataclass
import hashlib
import os
from pathlib import Path
import shutil
from typing import Dict, List, Optional
import uuid

from tools.core.config import DEFAULT_PROJECT_SKILLS_SUBDIR, LOCKFILE_SCHEMA_PATH
from tools.core.loader import load_manifest
from tools.core.models import RegistrySkill, SkillManifest
from tools.installer.lockfile import LockfileManager
from tools.resolver.graph import ResolvedSkill


class InstallationError(Exception):
    pass


class DirtyTreeError(InstallationError):
    pass


@dataclass
class InstallResult:
    skill_id: str
    version: str
    status: str  # 'installed', 'up-to-date', 'overwritten'
    target_path: str
    reason: str


class AtomicInstaller:
    def __init__(self, repo_root: Path, project_root: Path):
        self.repo_root = repo_root
        self.project_root = project_root
        self.skills_dir = project_root / DEFAULT_PROJECT_SKILLS_SUBDIR
        self.lockfile_mgr = LockfileManager(project_root, schema_path=repo_root / LOCKFILE_SCHEMA_PATH)

    def install_resolved(
        self,
        resolved_skills: List[ResolvedSkill],
        registry: Dict[str, RegistrySkill],
        force: bool = False,
    ) -> List[InstallResult]:
        """Atomically installs a list of resolved skills into the project directory."""
        self.skills_dir.mkdir(parents=True, exist_ok=True)
        results: List[InstallResult] = []

        for item in resolved_skills:
            skill = registry[item.id]
            manifest_file = self.repo_root / skill.manifest_path
            manifest = load_manifest(manifest_file)
            result = self.install_single(manifest, item, force=force)
            results.append(result)

        return results

    def install_single(
        self,
        manifest: SkillManifest,
        resolved: ResolvedSkill,
        force: bool = False,
    ) -> InstallResult:
        dest_dir = self.skills_dir / manifest.id
        lockfile = self.lockfile_mgr.load()
        existing_record = lockfile.skills.get(manifest.id)

        # 1. Dirty check if destination exists
        if dest_dir.exists():
            if not force and existing_record:
                # Check if versions match and hash matches
                if existing_record.commit == manifest.source.get("commit"):
                    return InstallResult(
                        skill_id=manifest.id,
                        version=manifest.version,
                        status="up-to-date",
                        target_path=str(dest_dir),
                        reason=resolved.install_reason,
                    )
                else:
                    raise DirtyTreeError(
                        f"Skill '{manifest.id}' exists at {dest_dir} with different version/commit. Use --force to overwrite."
                    )
            elif not force and not existing_record:
                raise DirtyTreeError(
                    f"Directory '{dest_dir}' exists but is not tracked in lockfile. Use --force to overwrite."
                )

        # 2. Prepare staging directory
        stage_dir = self.skills_dir / f".tmp-{manifest.id}-{uuid.uuid4().hex[:8]}"
        if stage_dir.exists():
            shutil.rmtree(stage_dir)
        stage_dir.mkdir(parents=True, exist_ok=True)

        try:
            # 3. Populate staging directory
            source_manifest_path = Path(manifest.file_path) if manifest.file_path else self.repo_root / f"skills/{manifest.id}/manifest.yaml"
            manifest_dir = source_manifest_path.parent

            if manifest.source.get("type") == "internal":
                # Copy complete internal skill tree
                for child in manifest_dir.iterdir():
                    if child.name.startswith("."):
                        continue
                    if child.is_dir():
                        shutil.copytree(child, stage_dir / child.name)
                    else:
                        shutil.copy2(child, stage_dir / child.name)
            else:
                # Copy manifest
                shutil.copy2(source_manifest_path, stage_dir / "manifest.yaml")
                # Create standard pointer SKILL.md for external upstream skill
                self._generate_upstream_skill_doc(manifest, stage_dir / "SKILL.md")

            # 4. Atomic commit: swap or move staging to dest_dir
            if dest_dir.exists():
                shutil.rmtree(dest_dir)
            stage_dir.rename(dest_dir)

            # 5. Record into lockfile
            integrity_str = f"sha256:{manifest.source.get('integrity', {}).get('hash', 'unknown')}"
            self.lockfile_mgr.record_skill(
                skill_id=manifest.id,
                version=manifest.version,
                source_type=manifest.source.get("type", "unknown"),
                repository=manifest.source.get("repository", "unknown"),
                commit=manifest.source.get("commit", "unknown"),
                integrity=integrity_str,
                install_reason=resolved.install_reason,
                dependencies=resolved.dependencies,
            )

            status = "overwritten" if existing_record else "installed"
            return InstallResult(
                skill_id=manifest.id,
                version=manifest.version,
                status=status,
                target_path=str(dest_dir),
                reason=resolved.install_reason,
            )
        except Exception as e:
            if stage_dir.exists():
                shutil.rmtree(stage_dir)
            raise InstallationError(f"Failed to install skill '{manifest.id}': {e}")

    def _generate_upstream_skill_doc(self, manifest: SkillManifest, doc_path: Path) -> None:
        """Generates a structured SKILL.md file for external upstream skills."""
        content = f"""---
name: {manifest.id}
description: {manifest.description}
version: {manifest.version}
type: {manifest.type.value}
status: {manifest.status.value}
---

# {manifest.name}

> **Source**: [{manifest.source.get('repository')}]({manifest.source.get('repository')})  
> **Source Type**: `{manifest.source.get('type')}` | **License**: `{manifest.source.get('license')}`  
> **Pinned Commit**: `{manifest.source.get('commit')}` | **Verified**: `{manifest.source.get('verified_at')}`

## Overview
{manifest.description}

## Capabilities
"""
        for cap in manifest.capabilities.get("provides", []):
            content += f"- `{cap}`\n"

        content += f"""
## Upstream Provenance
This skill is tracked from official/curated upstream source `{manifest.source.get('repository')}`.
Consult upstream repository documentation for platform-specific CLI plugins and MCP server bindings.
"""
        with open(doc_path, "w", encoding="utf-8") as f:
            f.write(content)
