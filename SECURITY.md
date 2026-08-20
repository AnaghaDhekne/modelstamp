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

For artifacts crossing a trust boundary, use the optional `signing_key`
argument. It authenticates the complete manifest and artifact digest with
HMAC-SHA-256. Protect the key independently of the artifact. Signed manifests
detect unauthorized replacement, but they do not sandbox pickle/joblib or
prevent malicious code in an artifact signed by a compromised or untrusted key.

HMAC is symmetric: signing and verification use the same secret. Anyone who
possesses the verification key can also forge a valid manifest, so HMAC keys
must not be published or distributed to verification-only consumers.
`modelstamp` does not currently provide asymmetric verification through
Ed25519, Sigstore, or another public-key signature system.

Use `key_id` on new artifacts and pass a `signing_keys` registry when loading to
rotate secrets without invalidating older models. The key identifier is itself
authenticated. Remove old registry entries only after their artifacts have
expired or been re-signed.
