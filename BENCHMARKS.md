# Verification benchmarks

`modelstamp.verify()` performs a streaming SHA-256 pass and therefore has
linear I/O cost and constant memory usage. The benchmark uses pre-created files,
warms filesystem caches once, and reports the median of three runs.

Run it on your deployment hardware:

```bash
python benchmarks/benchmark_verify.py --sizes 10 100 1024 --repeats 3
```

## Reference result

Environment: Codex Linux workspace, CPython 3.12, warm filesystem cache. These
numbers measure this environment only; storage and CPU will change results.

<!-- benchmark-results -->

| Size | Median time | Throughput |
|---:|---:|---:|
| 10 MiB | 0.032 s | 311.6 MiB/s |
| 100 MiB | 0.326 s | 307.1 MiB/s |
| 1024 MiB | 3.334 s | 307.1 MiB/s |

The nearly constant throughput demonstrates the expected linear scaling. The
benchmark measures a warm cache; cold storage and network filesystems can be
substantially slower.

Dependency-drift behavior has a separate CI-enforced matrix covering eight
pinned save/check environment pairs. See the
[dependency-drift validation matrix](https://anaghadhekne.github.io/modelstamp/drift-benchmarks/)
for scenarios, observed package changes, and reproduction instructions.
