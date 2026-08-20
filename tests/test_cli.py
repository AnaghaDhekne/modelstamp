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


def test_check_exit_statuses(tmp_path, capsys):
    path = tmp_path / "model.pkl"
    ms.save(DummyModel(), path, backend="pickle", include_git=False)

    assert main(["check", str(path)]) == 0
    assert "match" in capsys.readouterr().out

    path.write_bytes(path.read_bytes() + b"tampered")
    assert main(["check", str(path)]) == 1
    assert "integrity" in capsys.readouterr().out


def test_signed_verify_reads_key_from_environment(tmp_path, capsys, monkeypatch):
    path = tmp_path / "model.pkl"
    monkeypatch.setenv("MODELSTAMP_TEST_KEY", "test-secret")
    ms.save(DummyModel(), path, backend="pickle", signing_key=b"test-secret")

    assert (
        main(
            [
                "verify",
                str(path),
                "--signing-key-env",
                "MODELSTAMP_TEST_KEY",
            ]
        )
        == 0
    )
    assert "verified" in capsys.readouterr().out


def test_missing_signing_key_environment_variable_is_clean_error(tmp_path, capsys):
    assert (
        main(
            [
                "verify",
                str(tmp_path / "model.pkl"),
                "--signing-key-env",
                "MISSING_MODELSTAMP_KEY",
            ]
        )
        == 2
    )
    assert "is not set" in capsys.readouterr().err


def test_filesystem_errors_do_not_print_tracebacks(tmp_path, capsys, monkeypatch):
    path = tmp_path / "model.pkl"
    ms.save(DummyModel(), path, backend="pickle")

    def fail_read(*args, **kwargs):
        raise PermissionError("permission denied for test")

    monkeypatch.setattr("modelstamp.cli.verify", fail_read)
    assert main(["verify", str(path)]) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err.strip() == "modelstamp: permission denied for test"
