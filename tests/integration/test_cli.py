"""Integration tests for CLI entrypoints and arguments."""

import json
from tools.cli import main


def test_cli_list(capsys):
    ret = main(["list", "--json"])
    assert ret == 0
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert len(data) >= 8


def test_cli_search(capsys):
    ret = main(["search", "mongodb", "--json"])
    assert ret == 0
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert any(item["id"] == "mongodb" for item in data)


def test_cli_discover(capsys):
    ret = main(["discover", "build a production Node.js API with MongoDB", "--json"])
    assert ret == 0
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert "recommendations" in data
    assert any(r["id"] == "mongodb" for r in data["recommendations"])


def test_cli_validate(capsys):
    ret = main(["validate", "--json"])
    assert ret == 0
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["is_valid"] is True


def test_cli_install_and_update(capsys, temp_project):
    ret = main(["install", "testing", "--target", str(temp_project), "--json"])
    assert ret == 0
    _ = capsys.readouterr()  # Drain install output

    ret_update = main(["update", "--target", str(temp_project), "--json"])
    assert ret_update == 0
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert any(item["skill_id"] == "testing" for item in data)
