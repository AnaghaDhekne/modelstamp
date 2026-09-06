"""Create two pinned environments and run the complete experiment."""

from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
import venv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EXPERIMENT = Path(__file__).resolve().parent


def _python(environment: Path) -> Path:
    if sys.platform == "win32":
        return environment / "Scripts" / "python.exe"
    return environment / "bin" / "python"


def _run(command: list[str]) -> None:
    print("+", " ".join(command), flush=True)
    subprocess.run(command, cwd=ROOT, check=True)


def _create_environment(path: Path, requirements: Path) -> Path:
    venv.EnvBuilder(with_pip=True, clear=True).create(path)
    python = _python(path)
    _run(
        [
            str(python),
            "-m",
            "pip",
            "install",
            "--disable-pip-version-check",
            "-e",
            str(ROOT),
            "-r",
            str(requirements),
        ]
    )
    return python


def main() -> None:
    if sys.version_info[:2] != (3, 11):
        raise SystemExit(
            "this protocol is pinned to Python 3.11; "
            f"received {sys.version_info.major}.{sys.version_info.minor}"
        )
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=EXPERIMENT / "output",
        help="Directory for artifacts and JSON observations.",
    )
    args = parser.parse_args()
    output = args.output.resolve()
    artifacts = output / "artifacts"
    output.mkdir(parents=True, exist_ok=True)
    artifacts.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="modelstamp-sklearn-drift-") as temp:
        temporary = Path(temp)
        save_python = _create_environment(
            temporary / "save-control-env", EXPERIMENT / "requirements-save.txt"
        )
        _run(
            [
                str(save_python),
                str(EXPERIMENT / "create_artifacts.py"),
                "--output",
                str(artifacts),
            ]
        )
        _run(
            [
                str(save_python),
                str(EXPERIMENT / "observe.py"),
                "--condition",
                "control",
                "--artifacts",
                str(artifacts),
                "--output",
                str(output / "control.json"),
            ]
        )

        drift_python = _create_environment(
            temporary / "drift-env", EXPERIMENT / "requirements-drift.txt"
        )
        _run(
            [
                str(drift_python),
                str(EXPERIMENT / "observe.py"),
                "--condition",
                "drift",
                "--artifacts",
                str(artifacts),
                "--output",
                str(output / "drift.json"),
            ]
        )

    _run(
        [
            sys.executable,
            str(EXPERIMENT / "summarize_results.py"),
            "--control",
            str(output / "control.json"),
            "--drift",
            str(output / "drift.json"),
            "--output",
            str(output / "summary.json"),
        ]
    )


if __name__ == "__main__":
    main()
