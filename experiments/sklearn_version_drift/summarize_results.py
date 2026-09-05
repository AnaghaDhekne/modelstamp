"""Combine the independently generated control and drift observations."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--control", type=Path, required=True)
    parser.add_argument("--drift", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    control: Dict[str, Any] = json.loads(args.control.read_text(encoding="utf-8"))
    drift: Dict[str, Any] = json.loads(args.drift.read_text(encoding="utf-8"))
    assert control["condition"] == "control"
    assert drift["condition"] == "drift"

    baseline_drift = drift["baseline"]
    preload_drift = drift["modelstamp"]["preload_check"]
    strict_drift = drift["modelstamp"]["strict_load"]
    summary = {
        "protocol_version": 1,
        "save_sklearn": "1.5.2",
        "control_sklearn": control["environment"]["packages"]["scikit-learn"],
        "drift_sklearn": drift["environment"]["packages"]["scikit-learn"],
        "control": {
            "baseline_loaded": control["baseline"]["load_succeeded"],
            "modelstamp_check_mismatch": control["modelstamp"]["preload_check"][
                "mismatch"
            ],
            "modelstamp_strict_loaded": control["modelstamp"]["strict_load"][
                "load_succeeded"
            ],
        },
        "drift": {
            "baseline_reconstruction_started": baseline_drift["reconstruction_started"],
            "baseline_loaded": baseline_drift["load_succeeded"],
            "baseline_inconsistent_version_warning": baseline_drift[
                "inconsistent_version_warning"
            ],
            "baseline_predictions_match_save_environment": baseline_drift[
                "predictions_match_save_environment"
            ],
            "modelstamp_check_deserialized": preload_drift["deserialized"],
            "modelstamp_reported_changes": preload_drift["package_changes"],
            "modelstamp_strict_rejected": strict_drift["environment_mismatch_error"],
            "modelstamp_strict_deserialized": strict_drift["deserialized"],
        },
        "interpretation": (
            "For this pinned model and version pair, ordinary joblib/scikit-learn "
            "loading began reconstruction and surfaced version evidence during load. "
            "Modelstamp exposed the scikit-learn difference through a "
            "non-deserializing check and strict loading rejected before "
            "joblib.load was called."
        ),
    }
    args.output.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
