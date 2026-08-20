from __future__ import annotations

import json

import modelstamp as ms
from modelstamp.cli import main


class DummyModel:
    pass


def test_version_uses_package_version(capsys):
    try:
        main(["--version"])
    except SystemExit as exc:
        assert exc.code == 0
    assert capsys.readouterr().out.strip() == f"modelstamp {ms.__version__}"


def test_inspect_and_verify_commands(tmp_path, capsys):
    path = tmp_path / "model.pkl"
    ms.save(DummyModel(), path, backend="pickle", include_git=False)

    assert main(["inspect", str(path)]) == 0
    output = json.loads(capsys.readouterr().out)
    assert output["artifact"]["filename"] == "model.pkl"

    assert main(["verify", str(path)]) == 0
    assert capsys.readouterr().out.strip() == "Artifact integrity verified."


def test_errors_are_written_to_stderr(tmp_path, capsys):
    assert main(["verify", str(tmp_path / "missing.pkl")]) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "no manifest found" in captured.err
