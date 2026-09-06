# ADR-0005: Report compatibility evidence, not environment replication

- Status: Accepted; recorded retrospectively
- Recorded: 2026-09-06
- Owners: Modelstamp maintainers
- Related: `docs/dependency-drift.md`, `docs/comparisons.md`,
  `src/modelstamp/_environment.py`

## Context

Reproducing an ML result can require package resolution, operating-system
libraries, hardware, data, code, random state, and external services. A compact
artifact receipt cannot recreate all of these. Requirements files, lock files,
containers, and registries already address parts of environment construction
and lifecycle management.

## Decision

Modelstamp records and compares selected evidence about the save and load
runtimes. It reports differences and can apply a warn, raise, or ignore policy;
it does not install dependencies, resolve an environment, guarantee semantic
compatibility, or reproduce training.

Keep Modelstamp composable with lock files, containers, registries, and archived
research materials. Phrase a clean comparison as “no recorded relevant
difference,” not proof that two environments or behaviors are identical.

## Alternatives considered

### Capture the complete environment and recreate it

This would overlap environment managers and container systems, increase
platform-specific complexity, and still not guarantee reproducibility of data,
hardware, or external services.

### Require exact equality for all recorded fields

One global policy is easy to explain but prevents warning-only exploration and
makes platform metadata as decisive as a known model dependency.

### Record nothing beyond a dependency lock file

This helps rebuild an environment but does not connect that specification to
one artifact digest or provide a file-local verification gate.

## Consequences

### Benefits

- The package remains small and usable with existing environment tooling.
- Researchers can archive artifact-level evidence without claiming complete
  reproducibility.
- Consumers choose policy according to deployment risk.

### Costs and limitations

- Users must preserve separate environment and training materials when exact
  reproduction matters.
- Matching versions do not guarantee matching predictions or load success.
- Strict version equality may reject combinations that happen to be compatible.

## Evidence and follow-up

- Research-use guidance lists the additional data, code, environment, and
  validation outputs needed for an independently reproducible package.
- Drift experiments characterize selected version changes, not universal
  compatibility accuracy.

