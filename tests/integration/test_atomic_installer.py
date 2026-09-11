"""Integration tests for atomic installation and lockfile reproducibility."""

from pathlib import Path
from tools.installer.stage import AtomicInstaller, DirtyTreeError
from tools.resolver.graph import GraphResolver
from tools.installer.lockfile import LockfileManager


def test_atomic_install_creates_skills_and_lockfile(repo_root, registry, temp_project):
    installer = AtomicInstaller(repo_root, temp_project)
    resolver = GraphResolver(registry)
    resolved = resolver.resolve(["mongodb"], include_recommended=True)

    results = installer.install_resolved(resolved, registry)
    assert len(results) >= 2  # mongodb + testing

    # Verify directory contents
    skills_dir = temp_project / ".agents/skills"
    assert (skills_dir / "mongodb").is_dir()
    assert (skills_dir / "mongodb/manifest.yaml").is_file()
    assert (skills_dir / "mongodb/SKILL.md").is_file()

    # Verify lockfile
    lockfile_path = temp_project / ".agents/skills.lock.yaml"
    assert lockfile_path.is_file()

    lock_mgr = LockfileManager(temp_project)
    lock = lock_mgr.load()
    assert "mongodb" in lock.skills
    assert lock.skills["mongodb"].version == "1.2.0"
    assert lock.skills["mongodb"].integrity.startswith("sha256:")


def test_dirty_tree_protection(repo_root, registry, temp_project):
    installer = AtomicInstaller(repo_root, temp_project)
    resolver = GraphResolver(registry)
    resolved = resolver.resolve(["mongodb"], include_recommended=False)

    # 1. First install
    installer.install_resolved(resolved, registry)

    # 2. Modify local lockfile commit artificially to simulate drift
    lock_mgr = LockfileManager(temp_project)
    lock = lock_mgr.load()
    lock.skills["mongodb"].commit = "different-commit-12345"
    lock_mgr.save(lock)

    # 3. Attempt reinstall without force -> should raise DirtyTreeError
    import pytest
    with pytest.raises(DirtyTreeError):
        installer.install_resolved(resolved, registry, force=False)

    # 4. Attempt reinstall with force -> should succeed
    results = installer.install_resolved(resolved, registry, force=True)
    assert results[0].status == "overwritten"
