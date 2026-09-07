"""Validate the pre-submission artifact manifest using the standard library."""

from __future__ import annotations

import re
from pathlib import Path, PurePosixPath

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = REPOSITORY_ROOT / "ARTIFACT_CONTENTS.md"
START_MARKER = "<!-- artifact-paths:start -->"
END_MARKER = "<!-- artifact-paths:end -->"
PATH_PATTERN = re.compile(r"`([^`]+)`")
REQUIRED_CLAIMS = {"RQ1", "RQ2", "RQ3", "RQ4", "RQ5", "Supplementary"}


def validate(path: Path = MANIFEST_PATH) -> list[str]:
    text = path.read_text(encoding="utf-8")
    if text.count(START_MARKER) != 1 or text.count(END_MARKER) != 1:
        raise ValueError("artifact manifest must contain one path-marker pair")

    section = text.split(START_MARKER, 1)[1].split(END_MARKER, 1)[0]
    if not all(claim in section for claim in REQUIRED_CLAIMS):
        missing = sorted(claim for claim in REQUIRED_CLAIMS if claim not in section)
        raise ValueError(f"artifact manifest is missing claim groups: {missing}")

    paths = PATH_PATTERN.findall(section)
    if not paths:
        raise ValueError("artifact manifest contains no paths")
    duplicates = sorted({item for item in paths if paths.count(item) > 1})
    if duplicates:
        raise ValueError(f"artifact manifest contains duplicate paths: {duplicates}")

    for item in paths:
        candidate = PurePosixPath(item)
        if candidate.is_absolute() or ".." in candidate.parts:
            raise ValueError(f"artifact path must be repository-relative: {item}")
        if not (REPOSITORY_ROOT / candidate).exists():
            raise ValueError(f"artifact path does not exist: {item}")
    return paths


if __name__ == "__main__":
    validated = validate()
    print(f"artifact manifest valid: paths={len(validated)}")
