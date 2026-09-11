"""Tests checking registry integrity across all 6 validation gates."""

from tools.validator.engine import RegistryValidator


def test_full_registry_validation_passes():
    validator = RegistryValidator()
    report = validator.validate_all(strict=True)
    assert report.is_valid is True
    assert report.layer_errors == {}


def test_individual_gates():
    validator = RegistryValidator()
    from tools.validator.engine import ValidationReport

    r1 = ValidationReport(is_valid=True)
    validator.validate_layer_1_schemas(r1)
    assert r1.is_valid

    r2 = ValidationReport(is_valid=True)
    validator.validate_layer_2_referential(r2)
    assert r2.is_valid

    r3 = ValidationReport(is_valid=True)
    validator.validate_layer_3_graph_and_conflicts(r3)
    assert r3.is_valid

    r4 = ValidationReport(is_valid=True)
    validator.validate_layer_4_provenance(r4)
    assert r4.is_valid

    r5 = ValidationReport(is_valid=True)
    validator.validate_layer_5_content(r5)
    assert r5.is_valid

    r6 = ValidationReport(is_valid=True)
    validator.validate_layer_6_simulation(r6)
    assert r6.is_valid
