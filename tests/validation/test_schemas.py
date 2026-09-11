"""Validation tests verifying all schemas and manifest files."""

import jsonschema
from tools.core.config import SCHEMAS_DIR, REPO_ROOT
from tools.core.loader import load_json, load_yaml, validate_against_schema


def test_all_schemas_are_valid_draft202012():
    for schema_file in SCHEMAS_DIR.glob("*.json"):
        schema = load_json(schema_file)
        jsonschema.Draft202012Validator.check_schema(schema)


def test_registry_yaml_schema_conformance():
    reg_path = REPO_ROOT / "registry.yaml"
    schema_path = SCHEMAS_DIR / "registry.schema.json"
    errors = validate_against_schema(load_yaml(reg_path), schema_path)
    assert errors == []


def test_sources_yaml_schema_conformance():
    src_path = REPO_ROOT / "sources.yaml"
    schema_path = SCHEMAS_DIR / "sources.schema.json"
    errors = validate_against_schema(load_yaml(src_path), schema_path)
    assert errors == []


def test_all_manifests_conform_to_schema():
    schema_path = SCHEMAS_DIR / "manifest.schema.json"
    manifest_files = list(REPO_ROOT.glob("skills/**/manifest.yaml")) + list(
        REPO_ROOT.glob("engineering/**/manifest.yaml")
    ) + list(REPO_ROOT.glob("skills/observability/*.yaml"))
    assert len(manifest_files) >= 8

    for mf in manifest_files:
        errors = validate_against_schema(load_yaml(mf), schema_path)
        assert errors == [], f"Manifest {mf.name} failed schema validation: {errors}"
