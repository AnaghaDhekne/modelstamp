"""Run one save/check case for the dependency-drift validation matrix."""

from __future__ import annotations

import argparse
import json
from importlib import metadata
from pathlib import Path

import modelstamp as ms


def _fit_model(framework: str):
    features = [[0.0, 0.0], [0.0, 1.0], [1.0, 0.0], [1.0, 1.0]]
    target = [0, 0, 1, 1]
    if framework == "sklearn":
        from sklearn.linear_model import LogisticRegression
        from sklearn.pipeline import Pipeline
        from sklearn.preprocessing import StandardScaler

        return Pipeline(
            [("scale", StandardScaler()), ("model", LogisticRegression())]
        ).fit(features, target)
    if framework == "xgboost":
        from xgboost import XGBClassifier

        return XGBClassifier(n_estimators=2, max_depth=1, n_jobs=1).fit(
            features, target
        )
    if framework == "lightgbm":
        from lightgbm import LGBMClassifier

        return LGBMClassifier(n_estimators=2, max_depth=1, verbose=-1).fit(
            features, target
        )
    raise ValueError(f"unsupported framework: {framework}")


def _installed_versions(names: list[str]) -> dict[str, str | None]:
    versions: dict[str, str | None] = {}
    for name in names:
        try:
            versions[name] = metadata.version(name)
        except metadata.PackageNotFoundError:
            versions[name] = None
    return versions


def save_case(framework: str, artifact: Path, scenario: str) -> None:
    model = _fit_model(framework)
    manifest = ms.save(
        model,
        artifact,
        backend="joblib",
        include_git=False,
        metadata={"drift_scenario": scenario},
    )
    print(
        json.dumps(
            {
                "phase": "save",
                "scenario": scenario,
                "relevant_packages": manifest.relevant_packages,
                "versions": _installed_versions(manifest.relevant_packages),
            },
            sort_keys=True,
        )
    )


def check_case(artifact: Path, scenario: str, expected: set[str]) -> None:
    manifest = ms.inspect(artifact)
    report = ms.check(artifact)
    observed = {change.name for change in report.package_changes}
    result = {
        "phase": "check",
        "scenario": scenario,
        "expected_changes": sorted(expected),
        "observed_changes": sorted(observed),
        "relevant_packages": manifest.relevant_packages,
        "versions": _installed_versions(manifest.relevant_packages),
        "report": str(report),
        "passed": observed == expected and not report.runtime_changes,
    }
    print(json.dumps(result, sort_keys=True))
    if observed != expected:
        raise SystemExit(
            f"expected package changes {sorted(expected)}, observed {sorted(observed)}"
        )
    if report.runtime_changes:
        raise SystemExit(f"unexpected runtime changes: {report.runtime_changes}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=("save", "check"))
    parser.add_argument("--framework", choices=("sklearn", "xgboost", "lightgbm"))
    parser.add_argument("--artifact", type=Path, required=True)
    parser.add_argument("--scenario", required=True)
    parser.add_argument("--expected-changes", default="")
    args = parser.parse_args()

    if args.phase == "save":
        if args.framework is None:
            parser.error("--framework is required during save")
        save_case(args.framework, args.artifact, args.scenario)
    else:
        expected = {item for item in args.expected_changes.split(",") if item}
        check_case(args.artifact, args.scenario, expected)


if __name__ == "__main__":
    main()
