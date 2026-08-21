"""Save and verify an HMAC-authenticated Modelstamp artifact."""

import os
from pathlib import Path
from tempfile import TemporaryDirectory

import modelstamp as ms


def main() -> None:
    signing_key = os.environ.get("MODELSTAMP_SIGNING_KEY")
    if not signing_key:
        raise SystemExit("set MODELSTAMP_SIGNING_KEY before running this example")

    with TemporaryDirectory() as directory:
        path = Path(directory) / "signed-model.pkl"
        ms.save(
            {"coefficient": 1.25},
            path,
            backend="pickle",
            signing_key=signing_key.encode(),
            key_id="example-key",
        )

        ms.verify(path, signing_keys={"example-key": signing_key.encode()})
        restored, manifest = ms.load(
            path,
            signing_keys={"example-key": signing_key.encode()},
        )

        key_id = manifest.signature["key_id"] if manifest.signature else None
        print(f"Verified key: {key_id}")
        print(f"Restored object: {restored}")


if __name__ == "__main__":
    main()
