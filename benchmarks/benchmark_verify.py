"""Measure streaming verification throughput for representative artifact sizes."""

from __future__ import annotations

import argparse
import hashlib
import platform
import statistics
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

import modelstamp as ms

MIB = 1024 * 1024


def _create_artifact(directory: Path, size_mib: int) -> Path:
    path = directory / f"artifact-{size_mib}-mib.bin"
    block = b"\0" * MIB
    digest = hashlib.sha256()
    with path.open("wb") as stream:
        for _ in range(size_mib):
            stream.write(block)
            digest.update(block)

    manifest = ms.Manifest(
        artifact={
            "filename": path.name,
            "sha256": digest.hexdigest(),
            "size_bytes": size_mib * MIB,
        },
        serialization={"backend": "pickle"},
        model={"class": "BenchmarkArtifact", "module": "benchmarks"},
        environment={
            "python_version": platform.python_version(),
            "python_implementation": platform.python_implementation(),
            "platform": platform.platform(),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "packages": {},
        },
        relevant_packages=[],
    )
    path.with_name(path.name + ".manifest.json").write_text(
        manifest.to_json(), encoding="utf-8"
    )
    return path


def run(sizes: list[int], repeats: int) -> None:
    print("| Size | Median time | Throughput |")
    print("|---:|---:|---:|")
    with tempfile.TemporaryDirectory(prefix="modelstamp-benchmark-") as temporary:
        directory = Path(temporary)
        for size_mib in sizes:
            path = _create_artifact(directory, size_mib)
            ms.verify(path)  # Warm filesystem caches before measuring.
            durations = []
            for _ in range(repeats):
                started = time.perf_counter()
                ms.verify(path)
                durations.append(time.perf_counter() - started)
            median = statistics.median(durations)
            throughput = size_mib / median
            print(f"| {size_mib} MiB | {median:.3f} s | {throughput:.1f} MiB/s |")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sizes", nargs="+", type=int, default=[10, 100, 1024])
    parser.add_argument("--repeats", type=int, default=3)
    args = parser.parse_args()
    if any(size <= 0 for size in args.sizes) or args.repeats <= 0:
        parser.error("sizes and repeats must be positive")
    run(args.sizes, args.repeats)


if __name__ == "__main__":
    main()
