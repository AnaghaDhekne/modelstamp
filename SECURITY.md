# Security policy

## Supported versions

Until the first stable release, security fixes are applied to the latest
published version of `modelstamp`.

## Reporting a vulnerability

Please do not open a public issue for a suspected vulnerability. Report it by
email to `anaghagdhekne7@gmail.com` with:

- the affected version;
- a minimal reproduction or proof of concept;
- the expected and observed behavior; and
- any known impact or suggested mitigation.

The project aims to acknowledge reports within five business days. Once a fix
is available, the issue can be disclosed publicly with appropriate credit.

## Security boundary

`modelstamp` verifies artifact integrity against a sidecar checksum. A checksum
is not a signature: anyone able to replace both files can create a matching
pair. Pickle and joblib may execute arbitrary code while loading, so artifacts
must still come from a trusted source.
