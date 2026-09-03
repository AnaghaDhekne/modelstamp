import json
from pathlib import Path

import joblib
from side_effect_fixture import MarkerOnLoad

import modelstamp

ROOT = Path(__file__).resolve().parent
ARTIFACT = ROOT / "controlled.joblib"
MARKER = Path("/tmp/modelstamp_deserialization_marker")
RESULTS = ROOT / "results.json"


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


def force_relevant_drift():
    manifest = modelstamp.inspect(ARTIFACT)
    packages = manifest["environment"]["packages"]
    for package in packages:
        if package["name"].lower() == "joblib":
            package["version"] = "0.0.0-controlled-drift"
            break
    else:
        raise RuntimeError("joblib was not recorded in the manifest")

    # This experiment intentionally changes reference metadata only to create a
    # deterministic relevant-drift condition. It uses an unsigned manifest.
    manifest_path = ARTIFACT.with_suffix(ARTIFACT.suffix + ".modelstamp.json")
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "
", encoding="utf-8"
    )


def modelstamp_case():
    reset_marker()
    error = None
    try:
        modelstamp.load(ARTIFACT, strict=True)
    except Exception as exc:
        error = f"{type(exc).__name__}: {exc}"
    return {
        "path": "modelstamp.load(strict=True)",
        "rejected": error is not None,
        "marker_created": MARKER.exists(),
        "error": error,
    }


def conventional_case():
    reset_marker()
    error = None
    try:
        joblib.load(ARTIFACT)
    except Exception as exc:
        error = f"{type(exc).__name__}: {exc}"
    return {
        "path": "joblib.load",
        "rejected": error is not None,
        "marker_created": MARKER.exists(),
        "error": error,
    }


def main():
    save_fixture()
    force_relevant_drift()

    observations = [modelstamp_case(), conventional_case()]
    RESULTS.write_text(json.dumps(observations, indent=2) + "
", encoding="utf-8")
    print(json.dumps(observations, indent=2))

    modelstamp_result, conventional_result = observations
    assert modelstamp_result["rejected"]
    assert not modelstamp_result["marker_created"]
    assert conventional_result["marker_created"]


if __name__ == "__main__":
    main()
