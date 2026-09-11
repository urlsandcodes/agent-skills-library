# Engineering Agent Instructions

This document specifies how AI coding assistants (such as Claude Code, Cursor, Copilot, Gemini, and Antigravity) must interact with, consume, and contribute to the **Engineering Agent Skills Registry**.

---

## 1. Core Mission & Architectural Role

The Engineering Agent Skills Registry is a **master control plane, governance layer, and distribution mechanism** for engineering agent skills.

It is **NOT** a giant documentation dump. Its purpose is to:
1. Maintain a curated, machine-readable catalog of high-impact engineering skills.
2. Prefer **official vendor-maintained skills** whenever they exist.
3. Keep the master repository clean by referencing verified upstream sources rather than copying external code.
4. Maintain internal engineering intelligence skills (such as `architecture.system-validator`) where no vendor equivalent exists.
5. Provide deterministic, explainable discovery so agents only install the **minimal sufficient skill set** required for a task.
6. Keep project-specific architectural ground truth and local state strictly isolated from the master repository.

---

## 2. The Official-First Policy (Inviolable Invariant)

When selecting or adding skills, agents MUST strictly adhere to this provenance hierarchy:

```text
Priority 1: Official vendor-maintained Agent Skill (e.g. mongodb/agent-skills, flutter/agent-plugins, vercel/next.js)
Priority 2: Official vendor documentation / official repository specification
Priority 3: Highly trusted, curated community skill (e.g. Paldom/node-skills, samber/cc-skills-golang)
Priority 4: Custom internal skill maintained in this repository (e.g. architecture.system-validator)
```

> [!IMPORTANT]
> **Rule on Duplication**: Never create a custom replacement for an official or curated skill without an explicit, documented architectural justification in `sources.yaml`.

---

## 3. Skill Taxonomy

The registry explicitly classifies skills into three distinct types:

| Skill Type | Purpose | Examples | Ownership & Provenance |
| :--- | :--- | :--- | :--- |
| **`technology`** | Teaches idiomatic usage, syntax, APIs, and schemas for a specific language, framework, or database. | `mongodb`, `nodejs`, `nextjs`, `flutter`, `go` | Upstream vendor or curated community. |
| **`practice`** | Cross-cutting engineering disciplines spanning multiple technologies. | `testing`, `observability-instrumentation`, `observability-platform` | Standards bodies or community practice repositories. |
| **`intelligence`** | Metacognitive architectural reasoning, invariant auditing, and verification engines. | `architecture.system-validator` | Internal repository engineering team. |

---

## 4. Minimal Context & Project Isolation

### The Minimal Context Rule
AI context windows are precious. Agents working in a project codebase must **NEVER** install the entire master skill catalog.

Follow this workflow:
1. **Analyze Task**: Identify the exact technologies and engineering practices needed.
2. **Discover**: Run `skills discover "<task description>"` to receive explainable recommendations.
3. **Select Minimal Set**: Install only the 2 to 4 skills directly relevant to the feature.
4. **Isolate**: All installed skills live inside `.agents/skills/<skill-id>/`.

### Unified Project Directory Convention
All project-level agent artifacts must live under `.agents/`:
```text
my-project/
├── .agents/
│   ├── skills/
│   │   ├── mongodb/
│   │   ├── nodejs/
│   │   └── architecture.system-validator/
│   ├── skills.lock.yaml          # Pinned lockfile for reproducibility
│   └── architecture.md           # Living architectural ground truth
└── src/
```

> [!CAUTION]
> **Zero Project State in Master**: Never commit `.agents/architecture.md` or project lockfiles into this master repository. The master repository provides the skills; the project repository houses the project state.

---

## 5. Machine-Readable Contracts

### Registry Catalog: `registry.yaml`
The master index of all approved skills. Conforms to `schemas/registry.schema.json`.

### Provenance Registry: `sources.yaml`
Centralized upstream provenance tracking. Conforms to `schemas/sources.schema.json`. Every external source must specify:
- `provider`: Legal or organizational entity.
- `repository`: GitHub repository path (`owner/repo`).
- `source_type`: `official`, `curated_community`, or `internal`.
- `pinned_commit`: Immutable 40-character Git SHA (or `"local"` for internal).
- `license`: SPDX identifier.
- `verified_at`: ISO 8601 verification timestamp.

### Skill Manifest: `manifest.yaml`
Every skill maintains a contract conforming to `schemas/manifest.schema.json`:
- Declares unique `id`, semantic `version`, and `status`.
- Declares SHA-256 integrity hash (`source.integrity.hash`).
- Declares dependencies (`kind: hard`, `recommended`, or `optional`).
- Declares conflicts (`conflicts: []`).

---

## 6. How to Add a New Technology Skill

When instructed to register a new skill:
1. **Search Upstream**: Search for official vendor-maintained agent skills or official repositories.
2. **Verify Provenance**: Ensure the repository is maintained by the actual vendor (e.g. MongoDB Inc., Vercel, Google).
3. **Add to `sources.yaml`**: Record provider, repo, pinned commit, license, and verification date.
4. **Create Manifest**: Create `skills/<id>/manifest.yaml` adhering to `schemas/manifest.schema.json`.
5. **Register in `registry.yaml`**: Add skill entry with tags, dependencies, and category.
6. **Validate**: Run `./bin/skills validate --strict` to ensure all 6 validation gates pass.

---

## 7. Handling Upstream Evolution

When an official vendor skill is released for a technology previously served by a curated community skill:
1. Update `sources.yaml` to point to the new official vendor source.
2. Update `skills/<id>/manifest.yaml` with status `official`, new pinned commit, and SHA-256 digest.
3. Update `registry.yaml` with `status: official`.
4. Run validation and update regression test assertions.

---

## 8. CLI Command Quick Reference

```bash
# List all skills
./bin/skills list

# Search skills
./bin/skills search "mongodb"

# Explainable intent discovery
./bin/skills discover "build a production Go API with Prometheus metrics"

# View skill provenance and details
./bin/skills info mongodb

# Atomically install skills into project
./bin/skills install nodejs mongodb architecture.system-validator --target=../my-project

# Run 6-layer validation
./bin/skills validate --strict
```
