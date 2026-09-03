import json
from pathlib import Path

import joblib
from side_effect_fixture import MarkerOnLoad

import modelstamp
from modelstamp import EnvironmentMismatchError

ROOT = Path(__file__).resolve().parent
ARTIFACT = ROOT / "controlled.joblib"
MANIFEST = ARTIFACT.with_name(ARTIFACT.name + ".manifest.json")
MARKER = Path("/tmp/modelstamp_deserialization_marker")
RESULTS = ROOT / "results.json"
SENTINEL_VERSION = "0.0.0-controlled-drift"


def reset_marker():
    MARKER.unlink(missing_ok=True)


def save_fixture():
    reset_marker()
    modelstamp.save(
        MarkerOnLoad(),
        ARTIFACT,
        backend="joblib",
        include_git=False,
    )
    assert not MARKER.exists(), "fixture must not execute while being saved"


def establish_controlled_relevant_drift():
    manifest = modelstamp.inspect(ARTIFACT)
    packages = manifest.environment["packages"]
    if "joblib" not in packages:
        raise RuntimeError("joblib was not recorded in the manifest environment")

    current_joblib = packages["joblib"]
    if current_joblib == SENTINEL_VERSION:
        raise RuntimeError(
            "sentinel joblib version unexpectedly matches installed version"
        )

    # RQ4 isolates ordering after a known relevant mismatch has been established.
    # Relevance inference itself is evaluated separately by RQ1, so this synthetic
    # fixture explicitly designates joblib as relevant.
    manifest.relevant_packages = ["joblib"]
    packages["joblib"] = SENTINEL_VERSION
    MANIFEST.write_text(
        json.dumps(manifest.to_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return current_joblib


def assert_drift_precondition(current_joblib):
    report = modelstamp.check(ARTIFACT)
    joblib_changes = [
        change
        for change in report.package_changes
        if change.name == "joblib"
    ]
    assert len(joblib_changes) == 1, (
        "precondition must surface exactly one joblib package change"
    )
    change = joblib_changes[0]
    assert change.saved == SENTINEL_VERSION
    assert change.current == current_joblib
    return {
        "joblib": [change.saved, change.current],
    }


def modelstamp_case():
    reset_marker()
    try:
        modelstamp.load(
            ARTIFACT,
            on_mismatch="raise",
            return_manifest=False,
        )
    except EnvironmentMismatchError as exc:
        evidence = str(exc)
    else:
        raise AssertionError(
            "strict Modelstamp load unexpectedly reconstructed the drifted fixture"
        )

    assert "joblib" in evidence
    return {
        "path": 'modelstamp.load(on_mismatch="raise")',
        "rejected": True,
        "marker_created": MARKER.exists(),
        "mismatch_evidence": evidence,
    }


def conventional_case():
    reset_marker()
    joblib.load(ARTIFACT)
    return {
        "path": "joblib.load",
        "marker_created": MARKER.exists(),
    }


def main():
    save_fixture()
    current_joblib = establish_controlled_relevant_drift()
    precondition = assert_drift_precondition(current_joblib)

    modelstamp_result = modelstamp_case()
    conventional_result = conventional_case()

    observations = {
        "precondition_check_package_changes": precondition,
        "modelstamp_case": modelstamp_result,
        "conventional_case": conventional_result,
    }
    RESULTS.write_text(json.dumps(observations, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(observations, indent=2))

    assert modelstamp_result["rejected"]
    assert not modelstamp_result["marker_created"]
    assert conventional_result["marker_created"]


if __name__ == "__main__":
    main()
