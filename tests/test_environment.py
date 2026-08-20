from __future__ import annotations

from modelstamp._environment import capture_environment, collect_package_versions
from modelstamp._manifest import _diff_environments


def test_capture_environment_has_runtime_fields():
    environment = capture_environment(include_git=False)
    assert environment["python_version"]
    assert environment["python_implementation"]
    assert environment["platform"]
    assert environment["created_at"]
    assert isinstance(environment["packages"], dict)
    assert "git_commit" not in environment


def test_package_collection_omits_absent_distribution():
    versions = collect_package_versions(["definitely-not-a-real-package-xyz"])
    assert versions == {}


def test_package_collection_finds_installed_distribution():
    versions = collect_package_versions(["pytest"])
    assert versions["pytest"]


def test_diff_checks_only_relevant_packages():
    saved = {
        "python_version": "3.11.0",
        "python_implementation": "CPython",
        "platform": "example",
        "packages": {"numpy": "1.26.0"},
    }
    current = {
        "python_version": "3.11.0",
        "python_implementation": "CPython",
        "platform": "example",
        "packages": {"numpy": "2.0.0", "xgboost": "3.0.0"},
    }
    report = _diff_environments(saved, current, ["numpy"])
    assert len(report.package_changes) == 1
    assert report.package_changes[0].name == "numpy"


def test_new_irrelevant_package_does_not_trigger_mismatch():
    saved = {"python_version": "3.11.0", "packages": {}}
    current = {
        "python_version": "3.11.0",
        "packages": {"xgboost": "3.0.0"},
    }
    assert not _diff_environments(saved, current, [])


def test_runtime_changes_are_reported():
    saved = {
        "python_version": "3.11.0",
        "python_implementation": "CPython",
        "platform": "linux-a",
        "packages": {},
    }
    current = {
        "python_version": "3.12.0",
        "python_implementation": "CPython",
        "platform": "linux-b",
        "packages": {},
    }
    report = _diff_environments(saved, current, [])
    assert report
    assert len(report.runtime_changes) == 2
