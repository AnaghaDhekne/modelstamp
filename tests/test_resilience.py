"""Concurrency, fuzz, and adversarial regression tests."""

from __future__ import annotations

import json
import multiprocessing
import tempfile
from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

import modelstamp as ms
from modelstamp.exceptions import ManifestError


def _save_repeatedly(path: str, writer: int, start, errors) -> None:
    """Spawn-safe worker that repeatedly replaces one artifact pair."""
    try:
        if not start.wait(10):
            raise TimeoutError("concurrent-save start barrier timed out")
        for sequence in range(12):
            ms.save(
                {"writer": writer, "sequence": sequence},
                path,
                backend="pickle",
                include_git=False,
            )
    except BaseException as exc:  # pragma: no cover - reported in parent.
        errors.put(repr(exc))
        raise


def _read_repeatedly(path: str, start, errors) -> None:
    """Spawn-safe worker that verifies and loads during replacements."""
    try:
        if not start.wait(10):
            raise TimeoutError("concurrent-read start barrier timed out")
        for _ in range(24):
            ms.verify(path)
            value = ms.load(path, return_manifest=False)
            if not isinstance(value.get("sequence"), int):
                raise AssertionError(f"unexpected loaded value: {value!r}")
    except BaseException as exc:  # pragma: no cover - reported in parent.
        errors.put(repr(exc))
        raise


def _run_processes(processes, start, errors) -> None:
    for process in processes:
        process.start()
    start.set()
    for process in processes:
        process.join(20)
        if process.is_alive():
            process.terminate()
            process.join(5)
            pytest.fail(f"concurrent worker {process.name} did not terminate")
        assert process.exitcode == 0
    assert errors.empty(), errors.get()


def test_concurrent_process_saves_leave_one_valid_pair(tmp_path):
    path = tmp_path / "shared.pkl"
    context = multiprocessing.get_context("spawn")
    start = context.Event()
    errors = context.Queue()
    processes = [
        context.Process(
            target=_save_repeatedly,
            args=(str(path), writer, start, errors),
        )
        for writer in range(3)
    ]

    _run_processes(processes, start, errors)

    ms.verify(path)
    value = ms.load(path, return_manifest=False)
    assert value["writer"] in range(3)
    assert value["sequence"] == 11


def test_concurrent_process_reads_never_observe_a_mixed_pair(tmp_path):
    path = tmp_path / "shared.pkl"
    ms.save({"writer": -1, "sequence": -1}, path, include_git=False)
    context = multiprocessing.get_context("spawn")
    start = context.Event()
    errors = context.Queue()
    processes = [
        context.Process(
            target=_save_repeatedly,
            args=(str(path), 1, start, errors),
        ),
        context.Process(target=_read_repeatedly, args=(str(path), start, errors)),
        context.Process(target=_read_repeatedly, args=(str(path), start, errors)),
    ]

    _run_processes(processes, start, errors)
    ms.verify(path)


@given(st.binary(max_size=4096))
@settings(max_examples=300, deadline=None)
def test_arbitrary_manifest_bytes_fail_closed(payload):
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "model.pkl"
        path.write_bytes(b"not deserialized")
        path.with_name(path.name + ".manifest.json").write_bytes(payload)

        try:
            ms.inspect(path)
        except ManifestError:
            pass


@pytest.mark.parametrize(
    "filename",
    ["../model.pkl", "subdirectory/model.pkl", "subdirectory\\model.pkl"],
)
def test_manifest_filename_cannot_escape_the_artifact_directory(tmp_path, filename):
    path = tmp_path / "model.pkl"
    ms.save({"safe": True}, path, include_git=False)
    sidecar = path.with_name(path.name + ".manifest.json")
    manifest = json.loads(sidecar.read_text(encoding="utf-8"))
    manifest["artifact"]["filename"] = filename
    sidecar.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(ManifestError, match="must not contain directories"):
        ms.inspect(path)
