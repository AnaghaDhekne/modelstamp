# Verify model artifacts in CI/CD

Modelstamp's CLI can reject corrupted artifacts or incompatible deployment
environments before an application starts.

## Basic verification

```yaml
name: Verify model artifact

on:
  pull_request:

jobs:
  verify-model:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: python -m pip install modelstamp
      - run: modelstamp check artifacts/model.joblib
```

`check` returns a nonzero status for both integrity failures and relevant
runtime mismatches, making it appropriate for a required deployment check.

## Signed artifact verification

Store the HMAC key in the CI provider's secret store, not in the repository or
beside the model:

```yaml
      - name: Verify signed model
        env:
          MODELSTAMP_SIGNING_KEY: ${{ secrets.MODELSTAMP_SIGNING_KEY }}
        run: >-
          modelstamp verify artifacts/model.joblib
          --signing-key-env MODELSTAMP_SIGNING_KEY
```

Use separate keys for separate trust domains and rotate them with authenticated
key identifiers as described in the [signing guide](signing.md).

## What CI verification establishes

- The artifact bytes match the recorded size and SHA-256 digest.
- A configured HMAC validates under the supplied shared secret.
- The manifest follows the supported schema.
- `check` reports relevant runtime-version differences.

It does not establish that a pickle payload is safe to execute. CI should only
load artifacts produced by trusted workflows.

