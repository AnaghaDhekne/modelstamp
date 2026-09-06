# ADR-0002: Use a versioned JSON sidecar manifest

- Status: Accepted; recorded retrospectively
- Recorded: 2026-09-06
- Owners: Modelstamp maintainers
- Related: `src/modelstamp/_manifest.py`, `src/modelstamp/core.py`

## Context

Verification metadata must be readable without invoking the model's serializer.
Modelstamp must also retain ordinary pickle and joblib artifacts rather than
require conversion to a new container format.

## Decision

Store a schema-validated JSON manifest at `<artifact>.manifest.json`. The
manifest records a schema version, artifact filename, size and SHA-256,
serialization backend, model description, runtime evidence, relevant package
names, user metadata, and an optional HMAC record. Save operations stage both
files and commit the pair under an artifact lock.

Unknown schema versions and malformed required fields are rejected. Signature
bytes use deterministic JSON serialization rather than the displayed indented
representation.

## Alternatives considered

### Embed metadata inside the serialized object

This keeps one file, but reading the metadata would require entering the same
deserialization boundary that the verification design avoids.

### Define a new archive or model format

A container could keep payload and metadata together, but would replace
ordinary artifact workflows and make Modelstamp responsible for another
persistence format.

### Use a lock file alone

A lock file describes an environment but does not bind that record to the bytes
of one model artifact or identify its serializer.

## Consequences

### Benefits

- Humans and tools can inspect a stable, language-neutral record.
- Existing pickle/joblib tooling and filenames remain usable.
- Schema versioning makes incompatible format changes explicit.

### Costs and limitations

- Artifact and manifest are a pair that must be copied and retained together.
- Atomic replacement of two filesystem entries cannot provide a universal
  multi-file transaction across every filesystem and failure mode.
- An unsigned sidecar can be replaced together with its artifact.

## Evidence and follow-up

- Manifest property tests exercise malformed and non-canonical structures.
- Trust-boundary scenarios include manifest edits and pair replacement.
- Any incompatible manifest change requires a new ADR and schema-version plan.

