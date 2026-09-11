#!/usr/bin/env python3
"""Helper script for architecture.system-validator to validate finding JSON files against schema."""

import json
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
SCHEMA_PATH = SKILL_DIR / "schemas" / "finding.schema.json"


def main():
    if len(sys.argv) < 2:
        print("Usage: python validate_finding.py <path-to-finding.json>")
        sys.exit(1)

    finding_path = Path(sys.argv[1])
    if not finding_path.exists():
        print(f"Error: File not found {finding_path}")
        sys.exit(1)

    try:
        import jsonschema
    except ImportError:
        print("Warning: jsonschema not installed, performing basic JSON validation.")
        with open(finding_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        print("Valid JSON format.")
        sys.exit(0)

    with open(SCHEMA_PATH, "r", encoding="utf-8") as sf:
        schema = json.load(sf)

    with open(finding_path, "r", encoding="utf-8") as df:
        data = json.load(df)

    validator = jsonschema.Draft202012Validator(schema)
    errors = list(validator.iter_errors(data))

    if errors:
        print(f"Schema Validation FAILED ({len(errors)} errors):")
        for err in errors:
            print(f"  - {err.message}")
        sys.exit(2)
    else:
        print("Audit finding conforms strictly to finding.schema.json.")
        sys.exit(0)


if __name__ == "__main__":
    main()
