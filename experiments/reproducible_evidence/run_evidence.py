"""Run Modelstamp's drift and trust-boundary research evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
import tempfile
import venv
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
DRIFT_CASE = ROOT / "benchmarks" / "drift_matrix_case.py"
TRUST_CASE = ROOT / "examples" / "trust_boundary_matrix.py"


def _python(environment: Path) -> Path:
    return environment / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def _run(command: List[str], *, env: Dict[str, str] | None = None) -> str:
    print("+", " ".join(command), flush=True)
    completed = subprocess.run(
        command, cwd=ROOT, env=env, check=True, text=True, capture_output=True
    )
    if completed.stdout:
        print(completed.stdout, end="")
    return completed.stdout


def _last_json(output: str) -> Dict[str, Any]:
    lines = [line for line in output.splitlines() if line.strip()]
    return json.loads(lines[-1])


def _environment(cache: Path, specs: List[str]) -> Path:
    identity = hashlib.sha256("\0".join(specs).encode()).hexdigest()[:12]
    path = cache / identity
    python = _python(path)
    if not python.exists():
        venv.EnvBuilder(with_pip=True).create(path)
        _run(
            [
                str(python),
                "-m",
                "pip",
                "install",
                "--disable-pip-version-check",
                "-e",
                str(ROOT),
                *specs,
            ]
        )
    return python


def _run_drift(
    catalog: Dict[str, Any], output: Path, cache: Path, selected: set[str]
) -> List[Dict[str, Any]]:
    results = []
    for case in catalog["drift_scenarios"]:
        if selected and case["id"] not in selected:
            continue
        case_dir = output / "drift" / case["id"]
        case_dir.mkdir(parents=True, exist_ok=True)
        artifact = case_dir / "model.joblib"
        save_python = _environment(cache, case["save"])
        save = _last_json(
            _run(
                [
                    str(save_python),
                    str(DRIFT_CASE),
                    "save",
                    "--framework",
                    case["framework"],
                    "--scenario",
                    case["id"],
                    "--artifact",
                    str(artifact),
                ]
            )
        )
        check_python = _environment(cache, case["check"])
        check = _last_json(
            _run(
                [
                    str(check_python),
                    str(DRIFT_CASE),
                    "check",
                    "--scenario",
                    case["id"],
                    "--expected-changes",
                    ",".join(case["expected"]),
                    "--artifact",
                    str(artifact),
                ]
            )
        )
        result = {
            "definition": case,
            "save_observation": save,
            "check_observation": check,
        }
        (case_dir / "result.json").write_text(
            json.dumps(result, indent=2) + "\n", encoding="utf-8"
        )
        results.append(result)
    return results


def _run_trust(output: Path, cache: Path) -> Dict[str, Any]:
    result_path = output / "trust-boundary.json"
    python = _environment(cache, [])
    _run([str(python), str(TRUST_CASE), "--output", str(result_path)])
    return json.loads(result_path.read_text(encoding="utf-8"))


def _write_summary(output: Path, result: Dict[str, Any]) -> None:
    drift = result.get("drift", [])
    trust = result.get("trust_boundary", {}).get("results", [])
    passed = all(item["check_observation"]["passed"] for item in drift) and all(
        item["passed"] for item in trust
    )
    result["passed"] = passed
    (output / "results.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8"
    )
    drift_passes = sum(i["check_observation"]["passed"] for i in drift)
    trust_passes = sum(i["passed"] for i in trust)
    lines = [
        "# Modelstamp reproducible evidence",
        "",
        f"Overall: **{'PASS' if passed else 'FAIL'}**",
    ]
    if drift:
        lines.extend(
            [
                "",
                f"- Drift scenarios: {drift_passes}/{len(drift)} passed",
                "",
                "## Drift observations",
                "",
                "| Scenario | Expected | Observed | Result |",
                "| --- | --- | --- | --- |",
            ]
        )
        for item in drift:
            definition = item["definition"]
            observed = item["check_observation"]["observed_changes"]
            status = "PASS" if item["check_observation"]["passed"] else "FAIL"
            lines.append(
                f"| `{definition['id']}` | "
                f"{', '.join(definition['expected']) or 'none'} | "
                f"{', '.join(observed) or 'none'} | {status} |"
            )
    if trust:
        lines.extend(
            [
                "",
                f"- Trust-boundary scenarios: {trust_passes}/{len(trust)} passed",
                "",
                "## Trust-boundary observations",
                "",
                "| Scenario | Expected | Observed | Result |",
                "| --- | --- | --- | --- |",
            ]
        )
        for item in trust:
            lines.append(
                f"| {item['scenario']} | {item['expected']} | {item['observed']} | "
                f"{'PASS' if item['passed'] else 'FAIL'} |"
            )
    (output / "SUMMARY.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    if not passed:
        raise SystemExit("one or more evidence scenarios failed")


def main() -> None:
    if sys.version_info[:2] != (3, 11):
        raise SystemExit(
            "this protocol is pinned to Python 3.11; "
            f"received {sys.version_info.major}.{sys.version_info.minor}"
        )
    parser = argparse.ArgumentParser()
    parser.add_argument("--suite", choices=("all", "drift", "trust"), default="all")
    parser.add_argument("--scenario", action="append", default=[])
    parser.add_argument("--output", type=Path, default=HERE / "output")
    args = parser.parse_args()
    catalog = json.loads((HERE / "scenarios.json").read_text(encoding="utf-8"))
    known = {item["id"] for item in catalog["drift_scenarios"]}
    unknown = set(args.scenario) - known
    if unknown:
        parser.error(f"unknown drift scenario(s): {', '.join(sorted(unknown))}")
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    result: Dict[str, Any] = {
        "protocol_version": catalog["protocol_version"],
        "provenance": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "git_commit": _run(["git", "rev-parse", "HEAD"]).strip(),
            "scenario_catalog_sha256": hashlib.sha256(
                (HERE / "scenarios.json").read_bytes()
            ).hexdigest(),
        },
    }
    with tempfile.TemporaryDirectory(prefix="modelstamp-evidence-") as directory:
        cache = Path(directory) / "environments"
        if args.suite in ("all", "drift"):
            result["drift"] = _run_drift(catalog, output, cache, set(args.scenario))
        if args.suite in ("all", "trust"):
            result["trust_boundary"] = _run_trust(output, cache)
    _write_summary(output, result)


if __name__ == "__main__":
    main()
