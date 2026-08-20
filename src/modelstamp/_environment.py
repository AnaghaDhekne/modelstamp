"""Capture runtime and source-control metadata without importing ML packages."""

from __future__ import annotations

import platform
import subprocess
from datetime import datetime, timezone
from importlib import metadata
from typing import Dict, List, Optional

# Distributions commonly involved in tabular Python ML artifacts. Version
# discovery uses package metadata and therefore does not import these packages.
TRACKED_PACKAGES: List[str] = [
    "scikit-learn",
    "numpy",
    "scipy",
    "pandas",
    "xgboost",
    "lightgbm",
    "catboost",
    "joblib",
]


def _package_version(dist_name: str) -> Optional[str]:
    """Return the installed version of a distribution, or None if absent."""
    try:
        return metadata.version(dist_name)
    except metadata.PackageNotFoundError:
        return None


def collect_package_versions(
    packages: Optional[List[str]] = None,
) -> Dict[str, str]:
    """Return installed versions, omitting distributions that are absent."""
    names = packages if packages is not None else TRACKED_PACKAGES
    versions: Dict[str, str] = {}
    for name in names:
        version = _package_version(name)
        if version is not None:
            versions[name] = version
    return versions


def _git_commit() -> Optional[str]:
    """Return the current Git commit, or ``None`` outside a usable repository."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            timeout=3,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if result.returncode != 0:
        return None
    commit = result.stdout.strip()
    return commit or None


def _git_dirty() -> Optional[bool]:
    """Return whether the current Git worktree has uncommitted changes."""
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
            timeout=3,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if result.returncode != 0:
        return None
    return bool(result.stdout.strip())


def capture_environment(
    packages: Optional[List[str]] = None,
    include_git: bool = True,
) -> Dict[str, object]:
    """Build a snapshot of the environment relevant to model portability."""
    snapshot: Dict[str, object] = {
        "python_version": platform.python_version(),
        "python_implementation": platform.python_implementation(),
        "platform": platform.platform(),
        "packages": collect_package_versions(packages),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    if include_git:
        commit = _git_commit()
        if commit is not None:
            snapshot["git_commit"] = commit
            snapshot["git_dirty"] = _git_dirty()
    return snapshot
