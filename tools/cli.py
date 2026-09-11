#!/usr/bin/env python3
"""Unified CLI for the Engineering Agent Skills Registry.

Commands:
  list       - List registered skills in master catalog
  search     - Search skills by keyword, tag, or category
  discover   - Analyze task description and recommend minimal relevant skills
  info       - Show detailed manifest and provenance for a skill
  install    - Atomically install selected skills into project workspace (.agents/skills)
  update     - Check or apply updates against master registry
  validate   - Run 6-layer validation suite against master registry
"""

import argparse
import json
from pathlib import Path
import sys
from typing import List, Optional

# Add repo root to sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.core.config import REPO_ROOT as DEFAULT_REPO_ROOT
from tools.core.loader import load_registry, load_manifest, load_sources
from tools.search.engine import SearchEngine
from tools.discovery.recommender import DiscoveryEngine
from tools.resolver.graph import GraphResolver, ResolutionError, CyclicDependencyError, ConflictError
from tools.installer.stage import AtomicInstaller, DirtyTreeError, InstallationError
from tools.update.updater import SkillUpdater
from tools.validator.engine import RegistryValidator


def cmd_list(args: argparse.Namespace) -> int:
    registry = load_registry()
    filtered = []
    for s in registry.values():
        if args.type and s.type.value != args.type:
            continue
        if args.category and s.category.lower() != args.category.lower():
            continue
        if args.status and s.status.value != args.status:
            continue
        filtered.append(s)

    if args.json:
        out = [
            {
                "id": s.id,
                "name": s.name,
                "version": s.version,
                "type": s.type.value,
                "category": s.category,
                "status": s.status.value,
                "tags": s.tags,
                "description": s.description,
            }
            for s in filtered
        ]
        print(json.dumps(out, indent=2))
        return 0

    print(f"\nRegistered Engineering Agent Skills ({len(filtered)} total):\n")
    fmt = "{:<32} {:<14} {:<12} {:<20} {:<10}"
    print(fmt.format("SKILL ID", "TYPE", "STATUS", "CATEGORY", "VERSION"))
    print("-" * 92)
    for s in filtered:
        print(fmt.format(s.id, s.type.value, s.status.value, s.category, s.version))
    print()
    return 0


def cmd_search(args: argparse.Namespace) -> int:
    registry = load_registry()
    engine = SearchEngine(registry)
    results = engine.search(
        query=args.query,
        skill_type=args.type,
        category=args.category,
        status=args.status,
    )

    if args.json:
        print(json.dumps([r.to_dict() for r in results], indent=2))
        return 0

    print(f"\nSearch results for '{args.query}' ({len(results)} found):\n")
    for r in results:
        s = r.skill
        print(f"* {s.id} (score: {r.score:.1f})")
        print(f"  Name: {s.name} | Type: {s.type.value} | Status: {s.status.value}")
        print(f"  Category: {s.category} | Tags: {', '.join(s.tags)}")
        print(f"  Description: {s.description}")
        print()
    return 0


def cmd_discover(args: argparse.Namespace) -> int:
    registry = load_registry()
    engine = DiscoveryEngine(registry)
    recs = engine.discover(args.task_description)

    if args.json:
        print(
            json.dumps(
                {
                    "task": args.task_description,
                    "count": len(recs),
                    "recommendations": [r.to_dict() for r in recs],
                },
                indent=2,
            )
        )
        return 0

    print(f"\nExplainable Skill Discovery for task: \"{args.task_description}\"\n")
    if not recs:
        print("No specific engineering skills matched this task description.")
        return 0

    for r in recs:
        kind_label = r.kind.upper()
        print(f"[{kind_label}] {r.id} ({r.name}) - Confidence: {r.confidence:.0%}")
        print(f"  Type: {r.type} | Category: {r.category}")
        print("  Explainable Reasons:")
        for reason in r.reasons:
            print(f"    - {reason}")
        print()

    direct_ids = [r.id for r in recs if r.kind in ("direct", "governance")]
    print(f"Recommended install command:")
    print(f"  skills install {' '.join(direct_ids)}\n")
    return 0


def cmd_info(args: argparse.Namespace) -> int:
    registry = load_registry()
    if args.skill_id not in registry:
        print(f"Error: Skill '{args.skill_id}' not found in master catalog.", file=sys.stderr)
        return 1

    reg_skill = registry[args.skill_id]
    m_path = DEFAULT_REPO_ROOT / reg_skill.manifest_path
    manifest = load_manifest(m_path)
    sources = load_sources()
    source_record = sources.get(reg_skill.source_id)

    if args.json:
        data = {
            "id": manifest.id,
            "name": manifest.name,
            "version": manifest.version,
            "type": manifest.type.value,
            "status": manifest.status.value,
            "category": manifest.category,
            "description": manifest.description,
            "tags": manifest.tags,
            "provider": manifest.provider,
            "source": manifest.source,
            "capabilities": manifest.capabilities,
            "dependencies": [{"id": d.id, "kind": d.kind.value, "version": d.version} for d in manifest.dependencies],
            "conflicts": manifest.conflicts,
            "entrypoints": manifest.entrypoints,
        }
        if source_record:
            data["provenance"] = {
                "provider": source_record.provider,
                "repository": source_record.repository,
                "source_type": source_record.source_type.value,
                "pinned_commit": source_record.pinned_commit,
                "license": source_record.license,
                "verified_at": source_record.verified_at,
                "verification_notes": source_record.verification_notes,
            }
        print(json.dumps(data, indent=2))
        return 0

    print(f"\nSkill Details: {manifest.name} ({manifest.id})")
    print("=" * 60)
    print(f"Version:      {manifest.version}")
    print(f"Type:         {manifest.type.value}")
    print(f"Status:       {manifest.status.value}")
    print(f"Category:     {manifest.category}")
    print(f"Description:  {manifest.description}")
    print(f"Tags:         {', '.join(manifest.tags)}")
    print(f"Provider:     {manifest.provider.get('name')} ({manifest.provider.get('website', 'N/A')})")
    print(f"Upstream:     {manifest.source.get('repository')} (Commit: {manifest.source.get('commit', 'local')[:8]})")
    print(f"License:      {manifest.source.get('license')}")
    print(f"Verified:     {manifest.source.get('verified_at')}")

    if manifest.capabilities.get("provides"):
        print("\nCapabilities Provided:")
        for cap in manifest.capabilities["provides"]:
            print(f"  - {cap}")

    if manifest.dependencies:
        print("\nDependencies:")
        for d in manifest.dependencies:
            print(f"  - {d.id} ({d.kind.value}) {d.version or ''}")

    print()
    return 0


def cmd_install(args: argparse.Namespace) -> int:
    registry = load_registry()
    project_root = Path(args.target).resolve()

    resolver = GraphResolver(registry)
    try:
        resolved = resolver.resolve(
            args.skills,
            include_recommended=not args.no_recommended,
        )
    except CyclicDependencyError as e:
        print(f"Dependency Error: {e}", file=sys.stderr)
        return 3
    except ConflictError as e:
        print(f"Conflict Error: {e}", file=sys.stderr)
        return 3
    except ResolutionError as e:
        print(f"Resolution Error: {e}", file=sys.stderr)
        return 1

    if args.dry_run:
        plan = [
            {"id": r.id, "reason": r.install_reason, "dependencies": r.dependencies}
            for r in resolved
        ]
        if args.json:
            print(json.dumps({"dry_run": True, "plan": plan}, indent=2))
        else:
            print("\nDry Run: Installation Plan:")
            for item in plan:
                print(f"  * {item['id']} ({item['reason']})")
        return 0

    installer = AtomicInstaller(DEFAULT_REPO_ROOT, project_root)
    try:
        results = installer.install_resolved(resolved, registry, force=args.force)
    except DirtyTreeError as e:
        print(f"Dirty Tree Protection: {e}", file=sys.stderr)
        return 4
    except InstallationError as e:
        print(f"Installation Failure: {e}", file=sys.stderr)
        return 1

    if args.json:
        out = [
            {
                "skill_id": r.skill_id,
                "version": r.version,
                "status": r.status,
                "path": r.target_path,
                "reason": r.reason,
            }
            for r in results
        ]
        print(json.dumps({"success": True, "installed": out}, indent=2))
        return 0

    print(f"\nInstalled skills to '{project_root / '.agents/skills'}':\n")
    for r in results:
        print(f"  ✓ {r.skill_id} [{r.status}] ({r.reason})")
    print(f"\nLockfile written to '{project_root / '.agents/skills.lock.yaml'}'\n")
    return 0


def cmd_update(args: argparse.Namespace) -> int:
    registry = load_registry()
    project_root = Path(args.target).resolve()
    updater = SkillUpdater(DEFAULT_REPO_ROOT, project_root)

    if args.apply:
        results = updater.apply_updates(registry)
    else:
        results = updater.check_updates(registry)

    if args.json:
        print(json.dumps([r.to_dict() for r in results], indent=2))
        return 0

    print(f"\nSkill Update Status for '{project_root}':\n")
    for r in results:
        status_symbol = "✓" if r.status == "up-to-date" else "↑"
        print(
            f"  {status_symbol} {r.skill_id}: {r.status} "
            f"(installed: {r.installed_version}@{r.installed_commit[:7]}, "
            f"registry: {r.registry_version}@{r.registry_commit[:7]})"
        )
    print()
    if not args.apply and any(r.status == "update-available" for r in results):
        print("Run 'skills update --apply' to update to latest registered versions.")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    validator = RegistryValidator(DEFAULT_REPO_ROOT)
    report = validator.validate_all(strict=args.strict)

    if args.json:
        print(json.dumps(report.to_dict(), indent=2))
        return 0 if report.is_valid else 2

    print("\nRunning Registry 6-Layer Validation Suite...\n")
    for layer in range(1, 7):
        errs = report.layer_errors.get(layer, [])
        layer_names = {
            1: "Syntax & Schemas Gate",
            2: "Referential Integrity Gate",
            3: "Graph & Conflicts Gate",
            4: "Provenance & Integrity Gate",
            5: "Content Structure Gate",
            6: "Installation Simulation Gate",
        }
        name = layer_names.get(layer, f"Layer {layer}")
        if not errs:
            print(f"  ✓ Layer {layer}: {name} passed")
        else:
            print(f"  ✗ Layer {layer}: {name} FAILED ({len(errs)} errors):")
            for err in errs:
                print(f"      - {err}")

    print()
    if report.is_valid:
        print("All 6 validation gates passed successfully! Registry is valid.\n")
        return 0
    else:
        print("Validation FAILED. Please resolve errors listed above.\n")
        return 2


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="skills",
        description="Master Registry & Distribution Layer for Engineering Agent Skills",
    )
    parser.add_argument("--version", action="version", version="skills 1.0.0")
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # list
    p_list = subparsers.add_parser("list", help="List registered skills")
    p_list.add_argument("--type", choices=["technology", "practice", "intelligence"], help="Filter by type")
    p_list.add_argument("--category", help="Filter by category")
    p_list.add_argument("--status", choices=["official", "curated", "internal", "deprecated"], help="Filter by status")
    p_list.add_argument("--json", action="store_true", help="Output machine-readable JSON")

    # search
    p_search = subparsers.add_parser("search", help="Search skills by query")
    p_search.add_argument("query", nargs="?", default="", help="Search query")
    p_search.add_argument("--type", choices=["technology", "practice", "intelligence"])
    p_search.add_argument("--category", help="Filter by category")
    p_search.add_argument("--status", choices=["official", "curated", "internal", "deprecated"])
    p_search.add_argument("--json", action="store_true", help="Output machine-readable JSON")

    # discover
    p_discover = subparsers.add_parser("discover", help="Explainable intent-based skill recommendation")
    p_discover.add_argument("task_description", help="Natural language task description")
    p_discover.add_argument("--json", action="store_true", help="Output machine-readable JSON")

    # info
    p_info = subparsers.add_parser("info", help="View skill details and provenance")
    p_info.add_argument("skill_id", help="Skill ID")
    p_info.add_argument("--json", action="store_true", help="Output machine-readable JSON")

    # install
    p_install = subparsers.add_parser("install", help="Install skills into project workspace (.agents/skills)")
    p_install.add_argument("skills", nargs="+", help="Skill IDs to install")
    p_install.add_argument("--target", default=".", help="Target project root directory (default: current dir)")
    p_install.add_argument("--no-recommended", action="store_true", help="Exclude recommended dependencies")
    p_install.add_argument("--force", action="store_true", help="Overwrite existing local files")
    p_install.add_argument("--dry-run", action="store_true", help="Show resolution plan without installing")
    p_install.add_argument("--json", action="store_true", help="Output machine-readable JSON")

    # update
    p_update = subparsers.add_parser("update", help="Check or apply updates for installed skills")
    p_update.add_argument("--target", default=".", help="Target project root directory (default: current dir)")
    p_update.add_argument("--apply", action="store_true", help="Apply available updates")
    p_update.add_argument("--json", action="store_true", help="Output machine-readable JSON")

    # validate
    p_validate = subparsers.add_parser("validate", help="Run 6-layer validation on master registry")
    p_validate.add_argument("--strict", action="store_true", default=True, help="Enforce strict validation")
    p_validate.add_argument("--json", action="store_true", help="Output machine-readable JSON")

    args = parser.parse_args(argv)
    if not args.command:
        parser.print_help()
        return 0

    cmds = {
        "list": cmd_list,
        "search": cmd_search,
        "discover": cmd_discover,
        "info": cmd_info,
        "install": cmd_install,
        "update": cmd_update,
        "validate": cmd_validate,
    }

    handler = cmds.get(args.command)
    if not handler:
        parser.print_help()
        return 1

    return handler(args)


if __name__ == "__main__":
    sys.exit(main())
