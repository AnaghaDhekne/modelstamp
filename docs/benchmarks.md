# Benchmarks

Verification performs a streaming SHA-256 pass over the artifact, so its cost
is linear in file size and does not require loading the entire file into memory.

See [`BENCHMARKS.md`](https://github.com/AnaghaDhekne/modelstamp/blob/main/BENCHMARKS.md)
for measured results and the exact reproduction command. The benchmark script
is available at `benchmarks/benchmark_verify.py`.

